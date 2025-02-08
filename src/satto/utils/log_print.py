from colorama import Fore
from datetime import datetime

class LogPrint:
    """
    This class handles log writing and formating
    """

    def __init__(self, use_colors=True):
        self.use_colors = use_colors
        
    @staticmethod
    def red(msg):
        return Fore.RED + msg + Fore.RESET

    @staticmethod
    def yellow(msg):
        return Fore.YELLOW + msg + Fore.RESET

    @staticmethod
    def green(msg):
        return Fore.GREEN + msg + Fore.RESET

    @staticmethod
    def blue(msg):
        return Fore.BLUE + msg + Fore.RESET    

    @staticmethod
    def info(msg, with_time=True):
        if with_time:
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-5]            
            print(f"[{current_time}] {msg}")
        else:
            print(msg)

    def warning(self, msg):
        msg = self.yellow(msg) if self.use_colors else msg
        print(msg)

    def error(self, msg, should_exit=False):
        msg = self.red(msg) if self.use_colors else msg
        print(msg)
        if should_exit:
            raise SystemExit

    def header(self, header):
        header = self.green(header) if self.use_colors else header
        print("{s:{c}^{n}}".format(s=header, n=40, c="-"))
