import sys, os, subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QMessageBox, QLineEdit, QProgressBar, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices


# --- Thread ایمن برای اجرای PyInstaller ---
class ConverterThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(bool, str)

    def __init__(self, cmd, output_path):
        super().__init__()
        self.cmd = cmd
        self.output_path = output_path

    def run(self):
        try:
            process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for i, line in enumerate(iter(process.stdout.readline, '')):
                if not line:
                    break
                self.log_signal.emit(line.strip())
                self.progress_signal.emit(min(100, i // 5))
            process.wait()
            if process.returncode == 0:
                self.done_signal.emit(True, "✅ تبدیل با موفقیت انجام شد!")
            else:
                self.done_signal.emit(False, "❌ خطا در تبدیل! لطفاً لاگ را بررسی کنید.")
        except Exception as e:
            self.done_signal.emit(False, f"⚠️ خطای اجرا: {e}")


# --- رابط اصلی ---
class ExeConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Python to EXE Converter Pro")
        self.setGeometry(300, 100, 750, 520)
        self.setWindowIcon(QIcon("1.ico"))

        self.file_path = ""
        self.icon_path = ""
        self.output_path = os.path.dirname(os.path.abspath(__file__))  # پیش‌فرض: کنار خود برنامه

        # --- فایل ورودی ---
        self.file_label = QLabel("📂 انتخاب فایل Python:")
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.btn_browse = QPushButton("انتخاب فایل")

        # --- مسیر خروجی ---
        self.output_label = QLabel("📁 انتخاب محل خروجی:")
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setPlaceholderText("اگر چیزی انتخاب نکنید، خروجی کنار همین برنامه ذخیره می‌شود.")
        self.btn_output = QPushButton("انتخاب مسیر خروجی")

        # --- تنظیمات ---
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["One File (exe)", "One Dir (folder)"])
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Windowed (no console)", "Console Mode"])
        self.icon_btn = QPushButton("🎭 انتخاب آیکون")
        self.btn_convert = QPushButton("⚡ تبدیل به EXE")

        # --- خروجی ---
        self.progress = QProgressBar()
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)

        # --- چیدمان ---
        fbox = QHBoxLayout()
        fbox.addWidget(self.file_input)
        fbox.addWidget(self.btn_browse)

        obox = QHBoxLayout()
        obox.addWidget(self.output_input)
        obox.addWidget(self.btn_output)

        vbox = QVBoxLayout()
        vbox.addWidget(self.file_label)
        vbox.addLayout(fbox)
        vbox.addWidget(self.output_label)
        vbox.addLayout(obox)
        vbox.addWidget(self.mode_combo)
        vbox.addWidget(self.type_combo)
        vbox.addWidget(self.icon_btn)
        vbox.addWidget(self.btn_convert)
        vbox.addWidget(self.progress)
        vbox.addWidget(self.output_box)
        self.setLayout(vbox)

        # --- استایل ---
        self.setStyleSheet("""
        QWidget { background-color: #121212; color: white; font-size: 14px; }
        QPushButton { background-color: #222; color: white; border-radius: 8px; padding: 10px; }
        QPushButton:hover { background-color: #FF6600; }
        QLineEdit, QComboBox { background-color: #333; color: #eee; border: 1px solid #555; padding: 6px; }
        QTextEdit { background-color: #1e1e1e; color: #00FF00; border: 1px solid #444; }
        QProgressBar { background: #333; border-radius: 5px; text-align: center; color: white; }
        QProgressBar::chunk { background-color: #FF6600; }
        """)

        # --- اتصال دکمه‌ها ---
        self.btn_browse.clicked.connect(self.open_file)
        self.btn_output.clicked.connect(self.choose_output_folder)
        self.icon_btn.clicked.connect(self.choose_icon)
        self.btn_convert.clicked.connect(self.convert_file)

    # --- انتخاب فایل ---
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل Python", "", "Python Files (*.py)")
        if file_path:
            self.file_input.setText(file_path)
            self.file_path = file_path

    # --- انتخاب مسیر خروجی ---
    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب مسیر خروجی")
        if folder:
            self.output_input.setText(folder)
            self.output_path = folder

    # --- انتخاب آیکون ---
    def choose_icon(self):
        icon, _ = QFileDialog.getOpenFileName(self, "انتخاب آیکون", "", "Icon Files (*.ico)")
        if icon:
            self.icon_path = icon
            QMessageBox.information(self, "آیکون انتخاب شد ✅", icon)

    # --- اجرای PyInstaller ---
    def convert_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "⚠️", "لطفاً فایل Python را انتخاب کنید!")
            return

        # بررسی نصب PyInstaller
        try:
            subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], check=True, stdout=subprocess.PIPE)
        except Exception:
            QMessageBox.critical(self, "PyInstaller یافت نشد ❌",
                                 "لطفاً با این دستور نصبش کن:\n\npip install pyinstaller")
            return

        mode = "--onefile" if self.mode_combo.currentIndex() == 0 else "--onedir"
        window_mode = "--windowed" if self.type_combo.currentIndex() == 0 else "--console"

        cmd = [sys.executable, "-m", "PyInstaller", mode, window_mode, "--distpath", self.output_path]
        if self.icon_path:
            cmd.extend(["--icon", self.icon_path])
        cmd.append(self.file_path)

        self.output_box.clear()
        self.progress.setValue(0)
        self.output_box.append(f"📁 مسیر خروجی: {self.output_path}\n")
        self.output_box.append("🚀 شروع فرآیند تبدیل...\n")

        self.thread = ConverterThread(cmd, self.output_path)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.log_signal.connect(lambda t: self.output_box.append(t))
        self.thread.done_signal.connect(self.on_done)
        self.thread.start()

    # --- پایان کار ---
    def on_done(self, success, msg):
        if success:
            self.progress.setValue(100)
            self.output_box.append(msg)
            QMessageBox.information(self, "موفقیت ✅", f"{msg}\n📁 مسیر: {self.output_path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path))
        else:
            self.output_box.append(msg)
            QMessageBox.critical(self, "خطا ❌", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ExeConverter()
    w.show()
    sys.exit(app.exec())
