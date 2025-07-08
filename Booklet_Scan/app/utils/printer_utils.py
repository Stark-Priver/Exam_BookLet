import subprocess
import platform

# Configuration
DEFAULT_PRINTER_COMMAND = "lp"  # For CUPS (Linux/macOS)
WINDOWS_PRINTER_COMMAND = "PRINT" # This is a shell command, might need different handling

def print_pdf(file_path: str, printer_name: str = None, copies: int = 1) -> bool:
    """
    Sends a PDF file to the printer.

    Args:
        file_path (str): The absolute path to the PDF file to be printed.
        printer_name (str, optional): The name of the printer to use.
                                      If None, the system's default printer is used.
        copies (int, optional): Number of copies to print. Defaults to 1.

    Returns:
        bool: True if the print command was issued successfully, False otherwise.
    """
    if not file_path:
        print("Error: No file path provided for printing.")
        return False

    system = platform.system().lower()
    command = []

    if system == "linux" or system == "darwin": # Linux or macOS
        command.append(DEFAULT_PRINTER_COMMAND)
        if printer_name:
            command.extend(["-d", printer_name])
        if copies > 1:
            command.extend(["-n", str(copies)])
        command.append(file_path)
    elif system == "windows":
        # Printing on Windows via command line for PDF is tricky.
        # Acrobat Reader CLI, Foxit Reader CLI, or PowerShell's Out-Printer can be used.
        # For simplicity, we'll try a common approach if Acrobat Reader is installed and in PATH.
        # `PRINT /D:printer_name file_path` is for text files, not directly for PDFs without help.
        # A more robust Windows solution would involve PowerShell or a library like `win32print`.
        # This is a placeholder and might need adjustment based on available tools.
        # Using SumatraPDF is a good lightweight option if it can be assumed to be installed:
        # command.extend(["SumatraPDF.exe", "-print-to-default", "-silent", file_path])
        # command.extend(["SumatraPDF.exe", f'-print-to "{printer_name}"' if printer_name else "-print-to-default", "-silent", file_path])

        # For now, let's assume `lpr` might be available via WSL or a Windows port, or use a PowerShell alternative.
        # This basic example will likely fail on Windows without specific setup.
        # A better approach for Windows might be:
        # command = ["powershell", "-Command", f"Start-Process -FilePath \"{file_path}\" -Verb Print"]
        # if printer_name:
        #   command = ["powershell", "-Command", f"Get-Printer -Name \"{printer_name}\" | Out-Printer -InputObject \"{file_path}\""]
        # else:
        #   command = ["powershell", "-Command", f"Out-Printer -InputObject \"{file_path}\""]

        # Given the Raspberry Pi context, Windows is less likely. Sticking to lp/lpr logic.
        # If Windows support is critical, this part needs significant enhancement.
        print(f"Warning: Printing on Windows is not fully supported by this basic script. Attempting with '{WINDOWS_PRINTER_COMMAND}'.")
        command.append(WINDOWS_PRINTER_COMMAND) # This is unlikely to work for PDF directly
        if printer_name:
            command.extend([f"/D:{printer_name}"])
        command.append(file_path)
        # For a real Windows implementation, one might use:
        # command = ['cmd', '/c', 'start', '/min', 'AcroRd32.exe', '/t', file_path, printer_name]
        # This requires Adobe Reader and knowing its executable name.
    else:
        print(f"Error: Unsupported operating system '{system}' for printing.")
        return False

    try:
        print(f"Issuing print command: {' '.join(command)}")
        # Using shell=True can be a security risk if command components are from untrusted input.
        # Here, file_path and printer_name should be validated or sanitized if they come from external sources.
        # For internal use with controlled inputs, it's often accepted.
        # For `lp` and `lpr`, `shell=False` (the default) is generally safer.
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Print command stdout: {result.stdout}")
        if result.stderr:
            print(f"Print command stderr: {result.stderr}")
        return True
    except FileNotFoundError:
        print(f"Error: Print command '{command[0]}' not found. Ensure CUPS or printing software is installed and in PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error during printing: {e}")
        print(f"Command stdout: {e.stdout}")
        print(f"Command stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during printing: {e}")
        return False

if __name__ == '__main__':
    # This section is for testing the printer_utils.py script directly.
    # You'll need a PDF file to test with.
    # Create a dummy PDF file for testing if you don't have one.
    # For example, use the booklet.py script to generate one.

    print("Testing printer utility...")

    # Attempt to generate a test booklet to print
    # This requires `booklets.py` to be in Python's path or same directory
    # For simplicity, let's assume a test PDF exists or is created manually.

    # Create a dummy test file for printing
    test_pdf_path = "test_print_document.pdf"
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(test_pdf_path, pagesize=A4)
        c.drawString(100, 750, "Test Print Document")
        c.drawString(100, 700, "This is a test page from printer_utils.py.")
        c.save()
        print(f"Created dummy PDF for testing: {test_pdf_path}")

        print("\nAttempting to print to default printer...")
        if print_pdf(test_pdf_path):
            print("SUCCESS: Test print command issued to default printer.")
        else:
            print("FAILURE: Test print command to default printer failed.")

        # To test with a specific printer, uncomment and set your printer name
        # my_printer_name = "Your_Printer_Name_Here"
        # print(f"\nAttempting to print to specific printer: {my_printer_name}...")
        # if print_pdf(test_pdf_path, printer_name=my_printer_name):
        #     print(f"SUCCESS: Test print command issued to {my_printer_name}.")
        # else:
        #     print(f"FAILURE: Test print command to {my_printer_name} failed.")

        # Test with multiple copies
        # print("\nAttempting to print 2 copies to default printer...")
        # if print_pdf(test_pdf_path, copies=2):
        #     print("SUCCESS: Test print command for 2 copies issued.")
        # else:
        #     print("FAILURE: Test print command for 2 copies failed.")

    except ImportError:
        print("Could not import reportlab to create a test PDF. Please create 'test_print_document.pdf' manually to test printing.")
    except Exception as e:
        print(f"An error occurred in the test setup: {e}")
    finally:
        # Clean up the dummy file
        # import os
        # if os.path.exists(test_pdf_path):
        #     os.remove(test_pdf_path)
        #     print(f"Cleaned up dummy PDF: {test_pdf_path}")
        pass # Keep the test file for manual inspection if needed
```
