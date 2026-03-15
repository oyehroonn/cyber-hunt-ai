"""
Captcha solving integration for CyberAI platform.
Supports 2captcha, anticaptcha, and browser-based solving.
"""

import asyncio
import base64
from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger

from cyberAI.config import get_config


class CaptchaSolverBase(ABC):
    """Base class for captcha solvers."""
    
    @abstractmethod
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """Solve reCAPTCHA v2."""
        pass
    
    @abstractmethod
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> str:
        """Solve hCaptcha."""
        pass
    
    @abstractmethod
    async def solve_image_captcha(self, base64_img: str) -> str:
        """Solve image-based captcha."""
        pass


class TwoCaptchaSolver(CaptchaSolverBase):
    """2captcha.com solver implementation."""
    
    API_BASE = "https://2captcha.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """
        Solve reCAPTCHA v2 using 2captcha service.
        
        Args:
            site_key: The reCAPTCHA site key
            page_url: URL of the page with captcha
            
        Returns:
            Solved captcha token
        """
        import httpx
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            submit_url = f"{self.API_BASE}/in.php"
            params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1,
            }
            
            response = await client.get(submit_url, params=params)
            data = response.json()
            
            if data.get("status") != 1:
                logger.error(f"2captcha submit failed: {data}")
                return ""
            
            task_id = data.get("request")
            
            result_url = f"{self.API_BASE}/res.php"
            for _ in range(60):
                await asyncio.sleep(5)
                
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                }
                
                result_response = await client.get(result_url, params=result_params)
                result_data = result_response.json()
                
                if result_data.get("status") == 1:
                    return result_data.get("request", "")
                elif result_data.get("request") != "CAPCHA_NOT_READY":
                    logger.error(f"2captcha result error: {result_data}")
                    return ""
        
        logger.error("2captcha timeout")
        return ""
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> str:
        """Solve hCaptcha using 2captcha service."""
        import httpx
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            submit_url = f"{self.API_BASE}/in.php"
            params = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": site_key,
                "pageurl": page_url,
                "json": 1,
            }
            
            response = await client.get(submit_url, params=params)
            data = response.json()
            
            if data.get("status") != 1:
                logger.error(f"2captcha hcaptcha submit failed: {data}")
                return ""
            
            task_id = data.get("request")
            
            result_url = f"{self.API_BASE}/res.php"
            for _ in range(60):
                await asyncio.sleep(5)
                
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                }
                
                result_response = await client.get(result_url, params=result_params)
                result_data = result_response.json()
                
                if result_data.get("status") == 1:
                    return result_data.get("request", "")
                elif result_data.get("request") != "CAPCHA_NOT_READY":
                    logger.error(f"2captcha hcaptcha result error: {result_data}")
                    return ""
        
        return ""
    
    async def solve_image_captcha(self, base64_img: str) -> str:
        """Solve image captcha using 2captcha service."""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            submit_url = f"{self.API_BASE}/in.php"
            data = {
                "key": self.api_key,
                "method": "base64",
                "body": base64_img,
                "json": 1,
            }
            
            response = await client.post(submit_url, data=data)
            result = response.json()
            
            if result.get("status") != 1:
                logger.error(f"2captcha image submit failed: {result}")
                return ""
            
            task_id = result.get("request")
            
            result_url = f"{self.API_BASE}/res.php"
            for _ in range(30):
                await asyncio.sleep(3)
                
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                }
                
                result_response = await client.get(result_url, params=result_params)
                result_data = result_response.json()
                
                if result_data.get("status") == 1:
                    return result_data.get("request", "")
                elif result_data.get("request") != "CAPCHA_NOT_READY":
                    return ""
        
        return ""


class AntiCaptchaSolver(CaptchaSolverBase):
    """Anticaptcha.com solver implementation."""
    
    API_BASE = "https://api.anti-captcha.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """Solve reCAPTCHA v2 using anticaptcha service."""
        import httpx
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            create_task_url = f"{self.API_BASE}/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "RecaptchaV2TaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key,
                }
            }
            
            response = await client.post(create_task_url, json=payload)
            data = response.json()
            
            if data.get("errorId") != 0:
                logger.error(f"Anticaptcha create task failed: {data}")
                return ""
            
            task_id = data.get("taskId")
            
            get_result_url = f"{self.API_BASE}/getTaskResult"
            for _ in range(60):
                await asyncio.sleep(5)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id,
                }
                
                result_response = await client.post(get_result_url, json=result_payload)
                result_data = result_response.json()
                
                if result_data.get("status") == "ready":
                    solution = result_data.get("solution", {})
                    return solution.get("gRecaptchaResponse", "")
                elif result_data.get("errorId") != 0:
                    logger.error(f"Anticaptcha result error: {result_data}")
                    return ""
        
        return ""
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> str:
        """Solve hCaptcha using anticaptcha service."""
        import httpx
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            create_task_url = f"{self.API_BASE}/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key,
                }
            }
            
            response = await client.post(create_task_url, json=payload)
            data = response.json()
            
            if data.get("errorId") != 0:
                logger.error(f"Anticaptcha hcaptcha create task failed: {data}")
                return ""
            
            task_id = data.get("taskId")
            
            get_result_url = f"{self.API_BASE}/getTaskResult"
            for _ in range(60):
                await asyncio.sleep(5)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id,
                }
                
                result_response = await client.post(get_result_url, json=result_payload)
                result_data = result_response.json()
                
                if result_data.get("status") == "ready":
                    solution = result_data.get("solution", {})
                    return solution.get("gRecaptchaResponse", "")
                elif result_data.get("errorId") != 0:
                    return ""
        
        return ""
    
    async def solve_image_captcha(self, base64_img: str) -> str:
        """Solve image captcha using anticaptcha service."""
        import httpx
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            create_task_url = f"{self.API_BASE}/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "ImageToTextTask",
                    "body": base64_img,
                }
            }
            
            response = await client.post(create_task_url, json=payload)
            data = response.json()
            
            if data.get("errorId") != 0:
                logger.error(f"Anticaptcha image create task failed: {data}")
                return ""
            
            task_id = data.get("taskId")
            
            get_result_url = f"{self.API_BASE}/getTaskResult"
            for _ in range(30):
                await asyncio.sleep(3)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id,
                }
                
                result_response = await client.post(get_result_url, json=result_payload)
                result_data = result_response.json()
                
                if result_data.get("status") == "ready":
                    solution = result_data.get("solution", {})
                    return solution.get("text", "")
                elif result_data.get("errorId") != 0:
                    return ""
        
        return ""


class NoOpCaptchaSolver(CaptchaSolverBase):
    """No-op solver when no API key is configured."""
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        logger.warning("No captcha API key configured - skipping reCAPTCHA solve")
        return ""
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> str:
        logger.warning("No captcha API key configured - skipping hCaptcha solve")
        return ""
    
    async def solve_image_captcha(self, base64_img: str) -> str:
        logger.warning("No captcha API key configured - skipping image captcha solve")
        return ""


class CaptchaSolver:
    """
    Main captcha solver interface.
    Automatically selects the appropriate solver based on configuration.
    """
    
    def __init__(self):
        config = get_config()
        api_key = config.captcha_api_key
        service = config.captcha_service
        
        if not api_key:
            self._solver = NoOpCaptchaSolver()
            logger.info("No captcha API key configured - captcha solving disabled")
        elif service == "anticaptcha":
            self._solver = AntiCaptchaSolver(api_key)
            logger.info("Using anticaptcha solver")
        else:
            self._solver = TwoCaptchaSolver(api_key)
            logger.info("Using 2captcha solver")
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> str:
        """
        Solve reCAPTCHA v2.
        
        Args:
            site_key: The reCAPTCHA site key
            page_url: URL of the page with captcha
            
        Returns:
            Solved captcha token or empty string on failure
        """
        return await self._solver.solve_recaptcha_v2(site_key, page_url)
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> str:
        """
        Solve hCaptcha.
        
        Args:
            site_key: The hCaptcha site key
            page_url: URL of the page with captcha
            
        Returns:
            Solved captcha token or empty string on failure
        """
        return await self._solver.solve_hcaptcha(site_key, page_url)
    
    async def solve_image_captcha(self, base64_img: str) -> str:
        """
        Solve image-based captcha.
        
        Args:
            base64_img: Base64 encoded captcha image
            
        Returns:
            Solved captcha text or empty string on failure
        """
        return await self._solver.solve_image_captcha(base64_img)
    
    async def solve_captcha_in_page(self, page) -> bool:
        """
        Attempt to detect and solve captcha in a Playwright page.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if captcha was found and solved, False otherwise
        """
        try:
            recaptcha_frame = await page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_frame:
                src = await recaptcha_frame.get_attribute("src")
                if src:
                    import re
                    match = re.search(r'k=([A-Za-z0-9_-]+)', src)
                    if match:
                        site_key = match.group(1)
                        token = await self.solve_recaptcha_v2(site_key, page.url)
                        if token:
                            await page.evaluate(f'''
                                document.querySelector('[name="g-recaptcha-response"]').value = "{token}";
                                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                                    Object.keys(___grecaptcha_cfg.clients).forEach(key => {{
                                        const client = ___grecaptcha_cfg.clients[key];
                                        if (client && client.callback) {{
                                            client.callback("{token}");
                                        }}
                                    }});
                                }}
                            ''')
                            return True
            
            hcaptcha_frame = await page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha_frame:
                container = await page.query_selector('[data-sitekey]')
                if container:
                    site_key = await container.get_attribute("data-sitekey")
                    if site_key:
                        token = await self.solve_hcaptcha(site_key, page.url)
                        if token:
                            await page.evaluate(f'''
                                document.querySelector('[name="h-captcha-response"]').value = "{token}";
                                document.querySelector('[name="g-recaptcha-response"]').value = "{token}";
                            ''')
                            return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error attempting to solve captcha: {e}")
            return False


_captcha_solver: Optional[CaptchaSolver] = None


def get_captcha_solver() -> CaptchaSolver:
    """Get the global captcha solver instance."""
    global _captcha_solver
    if _captcha_solver is None:
        _captcha_solver = CaptchaSolver()
    return _captcha_solver


if __name__ == "__main__":
    async def main():
        solver = CaptchaSolver()
        print("Captcha solver initialized (no-op mode if no API key)")
        
        result = await solver.solve_recaptcha_v2("test-site-key", "https://example.com")
        print(f"reCAPTCHA result: '{result}'")
    
    asyncio.run(main())
