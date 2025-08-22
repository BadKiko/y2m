import asyncio
import logging
from typing import Optional, Dict, Any, List
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen

from app.core.config import settings

logger = logging.getLogger(__name__)

class ADBService:
    def __init__(self):
        self.devices: Dict[int, AdbDeviceTcp] = {}
        self.command_queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start ADB service and command processing"""
        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._process_command_queue())

    async def stop(self):
        """Stop ADB service"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for device in self.devices.values():
            try:
                device.close()
            except Exception:
                pass
        self.devices.clear()

    async def connect_device(self, device_id: int, ip: str, port: int = 5555) -> bool:
        """Connect to ADB device"""
        try:
            device = AdbDeviceTcp(ip, port)

            # Generate RSA key for authentication
            priv_key, pub_key = keygen()
            signer = PythonRSASigner(priv_key, pub_key)

            # Connect to device
            device.connect(rsa_keys=[signer], auth_timeout_s=10)

            self.devices[device_id] = device
            logger.info(f"Connected to ADB device {ip}:{port}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to ADB device {ip}:{port}: {e}")
            return False

    async def disconnect_device(self, device_id: int):
        """Disconnect from ADB device"""
        if device_id in self.devices:
            try:
                self.devices[device_id].close()
                del self.devices[device_id]
                logger.info(f"Disconnected from ADB device {device_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from ADB device {device_id}: {e}")

    async def execute_command(self, device_id: int, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute ADB command on device"""
        if device_id not in self.devices:
            return {
                "success": False,
                "error": f"Device {device_id} not connected",
                "output": "",
                "execution_time": 0.0
            }

        try:
            start_time = asyncio.get_event_loop().time()

            # Execute command
            result = await asyncio.wait_for(
                self._execute_shell_command(device_id, command),
                timeout=timeout
            )

            execution_time = asyncio.get_event_loop().time() - start_time

            return {
                "success": True,
                "output": result,
                "error": None,
                "execution_time": execution_time
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command execution timeout ({timeout}s)",
                "output": "",
                "execution_time": timeout
            }

        except Exception as e:
            logger.error(f"ADB command execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": 0.0
            }

    async def _execute_shell_command(self, device_id: int, command: str) -> str:
        """Execute shell command on ADB device"""
        device = self.devices[device_id]
        result = device.shell(command)
        return result

    async def queue_command(self, device_id: int, command: str, timeout: int = 30):
        """Add command to execution queue"""
        await self.command_queue.put({
            "device_id": device_id,
            "command": command,
            "timeout": timeout
        })

    async def _process_command_queue(self):
        """Process command queue"""
        while True:
            try:
                command_info = await self.command_queue.get()
                device_id = command_info["device_id"]
                command = command_info["command"]
                timeout = command_info["timeout"]

                logger.info(f"Processing ADB command for device {device_id}: {command}")

                result = await self.execute_command(device_id, command, timeout)

                # Here you could emit results via WebSocket or store in database
                if not result["success"]:
                    logger.error(f"ADB command failed: {result['error']}")

                self.command_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing ADB command queue: {e}")

    def get_connected_devices(self) -> List[int]:
        """Get list of connected device IDs"""
        return list(self.devices.keys())

# Global ADB service instance
adb_service = ADBService()
