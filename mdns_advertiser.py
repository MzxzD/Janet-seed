"""
mDNS advertiser for janet-seed WebSocket server.
Advertises _janet._tcp on local network for auto-discovery by CallJanet-iOS, Pixel, etc.
"""
import socket

try:
    from zeroconf import ServiceInfo, Zeroconf
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    Zeroconf = None
    ServiceInfo = None


class JanetMdnsAdvertiser:
    """Advertises janet-seed via mDNS (_janet._tcp) for local network discovery."""

    def __init__(self, service_name: str = "janet-seed", port: int = 8765):
        self.service_name = service_name
        self.service_type = "_janet._tcp"
        self.port = port
        self.zeroconf = None
        self.service_info = None

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def advertise(self) -> bool:
        if not ZEROCONF_AVAILABLE:
            return False
        try:
            self.zeroconf = Zeroconf()
            local_ip = self._get_local_ip()
            self.service_info = ServiceInfo(
                f"{self.service_type}.local.",
                f"{self.service_name}.{self.service_type}.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={"path": "/", "port": str(self.port)},
                server=f"{socket.gethostname()}.local.",
            )
            self.zeroconf.register_service(self.service_info)
            print(f"📢 mDNS: Advertising _janet._tcp at {local_ip}:{self.port}")
            return True
        except Exception as e:
            print(f"⚠️  mDNS advertise failed: {e}")
            return False

    def stop(self):
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception:
                pass
            self.zeroconf = None
            self.service_info = None
