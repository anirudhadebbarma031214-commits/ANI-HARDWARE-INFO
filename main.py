import json
import os
import platform
import subprocess
import sys
import psutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout

APP_NAME = "ANI HARDWARE INFO"

def run_powershell(script):
    if os.name != "nt":
        return []
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=8, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        raw = result.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        return data if isinstance(data, list) else [data]
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        return []

def ps_query(class_name, fields):
    return run_powershell("Get-CimInstance Win32_" + class_name + " | Select-Object " + ",".join(fields) + " | ConvertTo-Json -Compress")

def first_value(rows, key, fallback="Not reported"):
    if rows and isinstance(rows[0], dict):
        value = rows[0].get(key)
        if value not in (None, ""):
            return str(value).strip()
    return fallback

def bytes_text(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "Not reported"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def collect_info():
    cpu = ps_query("Processor", ["Name", "Manufacturer", "NumberOfCores", "NumberOfLogicalProcessors", "MaxClockSpeed"])
    computer = ps_query("ComputerSystem", ["Manufacturer", "Model", "TotalPhysicalMemory", "SystemType"])
    board = ps_query("BaseBoard", ["Manufacturer", "Product"])
    bios = ps_query("BIOS", ["Manufacturer", "SMBIOSBIOSVersion", "ReleaseDate"])
    gpu = ps_query("VideoController", ["Name", "AdapterRAM", "DriverVersion", "VideoModeDescription"])
    disks = ps_query("DiskDrive", ["Model", "Size", "MediaType", "InterfaceType"])
    os_info = ps_query("OperatingSystem", ["Caption", "Version", "OSArchitecture"])
    battery = ps_query("Battery", ["Name", "EstimatedChargeRemaining", "BatteryStatus"])
    vm = psutil.virtual_memory()
    volumes = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            volumes.append({"mount": part.mountpoint, "device": part.device, "total": bytes_text(usage.total),
                "used": bytes_text(usage.used), "free": bytes_text(usage.free), "percent": f"{usage.percent}%"})
        except (PermissionError, OSError):
            pass
    return {"cpu": cpu, "computer": computer, "board": board, "bios": bios, "gpu": gpu, "disks": disks,
        "os_info": os_info, "battery": battery, "cpu_name": first_value(cpu, "Name", platform.processor() or "Not reported"),
        "gpu_name": first_value(gpu, "Name", "Not reported"), "memory": vm, "memory_total": bytes_text(vm.total),
        "memory_used": bytes_text(vm.used), "memory_available": bytes_text(vm.available),
        "memory_percent": f"{vm.percent}%", "volumes": volumes, "python": platform.python_version()}

class InfoCard(QFrame):
    def __init__(self, title, value, detail=""):
        super().__init__()
        self.setObjectName("InfoCard")
        layout = QVBoxLayout(self)
        for text, name in [(title.upper(), "CardTitle"), (value, "CardValue"), (detail, "CardDetail")]:
            label = QLabel(text)
            label.setObjectName(name)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch()

class HardwareWindow(QMainWindow):
    PAGES = ["Overview", "CPU", "Memory", "Graphics", "Storage", "System"]
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1120, 760)
        self.data = {}
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        brand = QLabel("ANI\nHARDWARE INFO")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        subtitle = QLabel("SYSTEM INTELLIGENCE")
        subtitle.setObjectName("SideSubtitle")
        side.addWidget(subtitle)
        side.addSpacing(25)
        for name in self.PAGES:
            btn = QPushButton(name)
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, page=name: self.show_page(page))
            side.addWidget(btn)
        side.addStretch()
        self.refresh_button = QPushButton("↻   Refresh hardware")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.clicked.connect(self.refresh)
        side.addWidget(self.refresh_button)
        foot = QLabel("LIVE OS DATA  •  WINDOWS")
        foot.setObjectName("SideSubtitle")
        side.addWidget(foot)
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(28, 24, 28, 24)
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel("A live snapshot of the hardware reported by your computer.")
        self.page_subtitle.setObjectName("PageSubtitle")
        main_layout.addWidget(self.page_title)
        main_layout.addWidget(self.page_subtitle)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0, 18, 6, 6)
        self.scroll.setWidget(self.content)
        main_layout.addWidget(self.scroll)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(main_area, 1)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#08111f; color:#e8f3ff; font-family:'Segoe UI'; font-size:13px; }
            #Sidebar { background:#0b1728; border-right:1px solid #17304b; }
            #Brand { color:#43c8ff; font-size:24px; font-weight:800; letter-spacing:1px; }
            #SideSubtitle { color:#6f8ca8; font-size:10px; letter-spacing:1px; }
            #NavButton { text-align:left; padding:12px 14px; border:0; border-radius:7px; color:#9db5cb; background:transparent; font-size:14px; }
            #NavButton:hover { background:#132a43; color:#ffffff; }
            #RefreshButton { padding:12px; border:1px solid #1d8ac0; border-radius:7px; background:#0d3450; color:#64d6ff; font-weight:600; }
            #RefreshButton:hover { background:#124563; }
            #PageTitle { font-size:28px; font-weight:750; color:#f2f8ff; }
            #PageSubtitle { color:#8ba5bd; font-size:13px; }
            #InfoCard { background:#0d1b2d; border:1px solid #1c3855; border-radius:10px; min-height:118px; }
            #CardTitle { color:#63cfff; font-size:10px; font-weight:700; letter-spacing:1px; }
            #CardValue { color:#f3f8ff; font-size:18px; font-weight:650; }
            #CardDetail { color:#8ba5bd; font-size:12px; }
            #SectionTitle { color:#c9e8ff; font-size:15px; font-weight:700; padding:10px 0 5px; }
            #InfoLine { color:#c2d5e7; padding:8px 10px; background:#0d1b2d; border:1px solid #172f48; border-radius:6px; }
            QScrollBar:vertical { background:#08111f; width:9px; }
            QScrollBar::handle:vertical { background:#23435e; border-radius:4px; min-height:25px; }
        """)
        self.refresh()

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def section(self, title):
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        self.content_layout.addWidget(label)

    def card_grid(self, cards):
        holder = QWidget()
        grid = QGridLayout(holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)
        for i, card in enumerate(cards):
            grid.addWidget(InfoCard(*card), i // 2, i % 2)
        self.content_layout.addWidget(holder)

    def line(self, label, value):
        item = QLabel(f"{label}:   {value}")
        item.setObjectName("InfoLine")
        item.setWordWrap(True)
        self.content_layout.addWidget(item)

    def show_page(self, page):
        self.page_title.setText(page)
        self.clear_content()
        d = self.data
        cpu, computer, board, bios = d["cpu"], d["computer"], d["board"], d["bios"]
        gpu, disks, os_info, battery = d["gpu"], d["disks"], d["os_info"], d["battery"]
        self.page_subtitle.setText({
            "Overview":"A live snapshot of the hardware reported by your computer.",
            "CPU":"Processor details exposed by Windows CIM.",
            "Memory":"RAM capacity and current usage from the operating system.",
            "Graphics":"Display adapters detected by Windows; VRAM reporting may be incomplete.",
            "Storage":"Physical disks and mounted volume capacity.",
            "System":"Computer identity, firmware and operating-system information."
        }.get(page, "Hardware information"))
        if page == "Overview":
            self.card_grid([
                ("Processor", d["cpu_name"], f"{first_value(cpu,'NumberOfCores')} cores • {first_value(cpu,'NumberOfLogicalProcessors')} logical"),
                ("Memory", d["memory_total"], d["memory_percent"] + " used"),
                ("Graphics", d["gpu_name"], "Driver " + first_value(gpu, "DriverVersion")),
                ("Operating system", first_value(os_info,"Caption",platform.platform()), first_value(os_info,"OSArchitecture",platform.machine()))
            ])
            self.section("SYSTEM SUMMARY")
            self.line("Manufacturer", first_value(computer,"Manufacturer"))
            self.line("Model", first_value(computer,"Model"))
            self.line("Motherboard", first_value(board,"Product"))
            self.line("Memory available", d["memory_available"])
        elif page == "CPU":
            self.card_grid([
                ("Processor",d["cpu_name"],first_value(cpu,"Manufacturer")),
                ("Cores",first_value(cpu,"NumberOfCores"),"Physical cores reported by Windows"),
                ("Logical processors",first_value(cpu,"NumberOfLogicalProcessors"),"Threads reported by Windows"),
                ("Maximum clock",first_value(cpu,"MaxClockSpeed") + " MHz" if first_value(cpu,"MaxClockSpeed") != "Not reported" else "Not reported","Reported maximum")
            ])
            self.section("LIVE ACTIVITY")
            self.line("Current CPU utilization",f"{psutil.cpu_percent(interval=0.25)}%")
            self.line("Architecture",platform.machine())
        elif page == "Memory":
            vm = d["memory"]
            self.card_grid([("Total memory",d["memory_total"],"OS-reported physical memory"),("In use",d["memory_used"],d["memory_percent"]+" of total"),("Available",d["memory_available"],"Available to applications"),("Usage",d["memory_percent"],"Refresh for a new reading")])
            self.section("MEMORY DETAILS")
            self.line("Total bytes",str(vm.total))
            self.line("Available bytes",str(vm.available))
        elif page == "Graphics":
            if not gpu:
                self.line("Graphics adapter","Windows did not return adapter information.")
            for i,item in enumerate(gpu,1):
                self.section(f"GRAPHICS ADAPTER {i}")
                for label,key in [("Name","Name"),("VRAM (reported bytes)","AdapterRAM"),("Driver version","DriverVersion"),("Display mode","VideoModeDescription")]:
                    self.line(label,str(item.get(key) or "Not reported"))
        elif page == "Storage":
            self.section("PHYSICAL DISKS")
            if not disks:
                self.line("Physical disks","No disk details returned by Windows.")
            for i,item in enumerate(disks,1):
                self.section(f"DISK {i}")
                self.line("Model",str(item.get("Model") or "Not reported"))
                self.line("Capacity",bytes_text(item.get("Size")))
                self.line("Media type",str(item.get("MediaType") or "Not reported"))
                self.line("Interface",str(item.get("InterfaceType") or "Not reported"))
            self.section("MOUNTED VOLUMES")
            if not d["volumes"]:
                self.line("Volumes","No accessible mounted volumes found.")
            for v in d["volumes"]:
                self.line(v["mount"],f'{v["used"]} used / {v["total"]} total • {v["percent"]} • {v["free"]} free')
        else:
            self.section("COMPUTER")
            for label,key in [("Manufacturer","Manufacturer"),("Model","Model"),("System type","SystemType")]:
                self.line(label,first_value(computer,key))
            self.section("MOTHERBOARD")
            for label,key in [("Manufacturer","Manufacturer"),("Product","Product")]:
                self.line(label,first_value(board,key))
            self.section("BIOS / FIRMWARE")
            for label,key in [("Manufacturer","Manufacturer"),("Version","SMBIOSBIOSVersion"),("Release date","ReleaseDate")]:
                self.line(label,first_value(bios,key))
            self.section("OPERATING SYSTEM")
            for label,key in [("Name","Caption"),("Version","Version"),("Architecture","OSArchitecture")]:
                self.line(label,first_value(os_info,key,platform.platform() if key=="Caption" else "Not reported"))
            self.section("BATTERY")
            if battery:
                self.line("Name",first_value(battery,"Name"))
                charge = first_value(battery,"EstimatedChargeRemaining")
                self.line("Estimated charge",charge + "%" if charge != "Not reported" else charge)
                self.line("Status code",first_value(battery,"BatteryStatus"))
            else:
                self.line("Battery","No battery detected or Windows did not report one.")
            self.section("RUNTIME")
            self.line("Python version",d["python"])
            self.line("Machine architecture",platform.machine())

    def refresh(self):
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Reading hardware…")
        QApplication.processEvents()
        self.data = collect_info()
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("↻   Refresh hardware")
        current = self.page_title.text()
        self.show_page(current if current in self.PAGES else "Overview")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = HardwareWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
