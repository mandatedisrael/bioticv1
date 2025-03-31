import os
import asyncio
from pyppeteer import launch
import logging
import re

async def convert_webpage_to_pdf(url, output_dir='pdfs'):

    def sanitize_filename(url):

        # Remove protocol
        filename = re.sub(r'^https?://', '', url)
        # Replace non-alphanumeric characters with underscores
        filename = re.sub(r'[^a-zA-Z0-9_]', '_', filename)
        # Trim to reasonable length
        return filename[:255] + '.pdf'

    try:
        # Create full path, including any nested directories
        full_path = os.path.join(output_dir, sanitize_filename(url))
        
        # Ensure the full directory path exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Launch browser
        browser = await launch({
            'headless': True,
            'args': ['--no-sandbox', '--disable-setuid-sandbox']
        })
        
        # Create a new page
        page = await browser.newPage()
        
        # Set larger viewport for better PDF quality
        await page.setViewport({'width': 1200, 'height': 800})
        
        # Navigate to the URL
        try:
            await page.goto(url, {
                'waitUntil': 'networkidle0',
                'timeout': 30000  # 30 seconds timeout
            })
        except Exception as nav_error:
            logging.error(f"Navigation error for {url}: {nav_error}")
            await browser.close()
            return None
        
        # Generate PDF
        await page.pdf({
            'path': full_path,
            'format': 'A4',
            'printBackground': True,
            'margin': {
                'top': '0.5cm',
                'bottom': '0.5cm',
                'left': '0.5cm',
                'right': '0.5cm'
            }
        })
        
        # Close browser
        await browser.close()
        
        print(f"PDF generated: {full_path}")
        return full_path
    
    except Exception as e:
        logging.error(f"Error converting {url} to PDF: {e}")
        return None

async def convert_multiple_urls(urls):
    # Use asyncio.gather to run conversions concurrently
    pdf_paths = await asyncio.gather(
        *[convert_webpage_to_pdf(url) for url in urls]
    )
    return [path for path in pdf_paths if path]

def main():
    # Use the URLs you want to convert
    # urls = [
    #     "https://blog.symbiotic.fi/symbiotic-arrives-on-mainnet/",
    #     "https://docs.symbiotic.fi/modules/registries",
    #     "https://docs.symbiotic.fi/modules/extensions/burners",
    #     "https://docs.symbiotic.fi/guides/cli",
    #     "https://docs.symbiotic.fi/points-season2"
    # ]

    urls = [
        "https://docs.symbiotic.fi/modules/vault/accounting"
    ]
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Use asyncio.run() for modern Python async handling
    try:
        pdf_paths = asyncio.run(convert_multiple_urls(urls))
        
        print("Conversion complete. PDF files:")
        for path in pdf_paths:
            print(path)
    except Exception as e:
        logging.error(f"Conversion failed: {e}")

if __name__ == "__main__":
    main()