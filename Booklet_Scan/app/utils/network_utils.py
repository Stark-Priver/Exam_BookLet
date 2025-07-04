import socket
import subprocess
import platform

def get_ip_address():
    """
    Attempts to get the primary IP address of the machine.
    Prefers the IP address from 'hostname -I' if available (common on Linux).
    Falls back to a socket-based method.
    Returns a string with the IP address or a message if not found/error.
    """
    ip_address = "IP Not Found"
    system = platform.system()

    if system == "Linux":
        try:
            # Try 'hostname -I' first, as it often gives the most relevant IP
            # and handles multiple interfaces well (we take the first one)
            result = subprocess.check_output(['hostname', '-I'], universal_newlines=True).strip()
            if result:
                # Take the first IP address if multiple are listed
                ip_address = result.split(' ')[0]
                return ip_address
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback if hostname command fails or is not found
            pass  # Continue to socket method

    # General method using sockets (works on most platforms, but might give localhost)
    # This is a fallback or primary method for non-Linux systems.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0) # Non-blocking
        # Doesn't actually send data, but connects to a remote host to find preferred interface
        # Using Google's DNS server as a common remote host
        s.connect(('8.8.8.8', 80)) # connect() for UDP doesn't send packets
        ip_address = s.getsockname()[0]
        s.close()
    except Exception:
        # If the socket method fails, try to get localhost as a last resort for local dev
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            ip_address = "127.0.0.1" # Default if all else fails
            if system == "Linux": # Be more specific if it's Linux and previous methods failed
                 ip_address = "IP Error on Linux"

    if not ip_address or ip_address == "0.0.0.0":
        if system == "Linux":
            return "No network connection?"
        else:
            return "IP Not Found or Not Connected"

    return ip_address

if __name__ == '__main__':
    # Test the function
    print(f"System: {platform.system()}")
    ip = get_ip_address()
    print(f"Current IP Address: {ip}")
