import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# Function to download a file with timeout and error handling
def download_file(file_url, save_path, timeout=15):
    try:
        response = requests.get(file_url, stream=True, timeout=timeout)
        print(f"  {Fore.YELLOW}Status Code for {file_url}: {response.status_code}")
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"    {Fore.GREEN}Success: {file_url}\n")
            return True
        else:
            print(f"    {Fore.RED}Failed (HTTP {response.status_code}): {file_url}\n")
            return False
    except requests.exceptions.Timeout:
        print(f"    {Fore.RED}Timeout: {file_url}\n")
        return False
    except Exception as e:
        print(f"    {Fore.RED}Error downloading {file_url}: {e}\n")
        return False

# Function to crawl through directories and download files with timeout for requests
def crawl_and_download(base_url, current_url, visited_urls, save_dir, timeout=15):
    successful_downloads = 0
    failed_downloads = 0

    if current_url in visited_urls:
        return successful_downloads, failed_downloads

    visited_urls.add(current_url)

    try:
        # Send HTTP GET request to the directory URL with timeout
        response = requests.get(current_url, timeout=timeout)
        print(f"\n{Fore.CYAN}--- Accessing: {current_url} ---")
        print(f"  Status Code: {response.status_code}\n")

        if response.status_code != 200:
            print(f"    {Fore.RED}Failed to access {current_url} (HTTP {response.status_code})\n")
            return successful_downloads, failed_downloads
    except requests.exceptions.Timeout:
        print(f"    {Fore.RED}Timeout while trying to access: {current_url}\n")
        return successful_downloads, failed_downloads
    except Exception as e:
        print(f"    {Fore.RED}Error accessing {current_url}: {e}\n")
        return successful_downloads, failed_downloads

    # Parse the HTML content of the directory listing
    soup = BeautifulSoup(response.text, 'html.parser')

    # Loop through all anchor tags to find files and subdirectories
    for link in soup.find_all('a'):
        href = link.get('href')

        if href:
            # Construct the full URL
            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)

            # Check if the link is a file or a subdirectory
            if href.endswith('/'):  # It's a subdirectory, recurse into it
                subdir_path = os.path.join(save_dir, os.path.basename(parsed_url.path))
                os.makedirs(subdir_path, exist_ok=True)
                print(f"\n{Fore.GREEN}Entering subdirectory: {os.path.basename(subdir_path)}\n")
                sub_success, sub_failed = crawl_and_download(base_url, full_url, visited_urls, subdir_path, timeout)
                successful_downloads += sub_success
                failed_downloads += sub_failed
            else:  # It's a file to download (no extension filter)
                file_name = os.path.basename(parsed_url.path)
                file_path = os.path.join(save_dir, file_name)
                if download_file(full_url, file_path, timeout):
                    successful_downloads += 1
                else:
                    failed_downloads += 1

    return successful_downloads, failed_downloads

# Main function
def main():
    # Ask the user for the base URL
    base_url = input("Enter the URL of the directory you want to crawl (e.g., http://example.com/directory/): ").strip()
    
    # Validate the base URL
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Ask the user for the directory where the files should be saved
    save_dir = input("Enter the directory where you want to save the downloaded files (default is 'downloads'): ").strip()
    
    if not save_dir:
        save_dir = 'downloads'  # Default save directory
    
    # Create the save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    visited_urls = set()  # Set to track visited URLs

    print("\nStarting download process...\n")
    successful_downloads, failed_downloads = crawl_and_download(base_url, base_url, visited_urls, save_dir)

    # Print summary
    print(f"\n{Fore.MAGENTA}--- Download Summary ---")
    print(f"  Total Successful Downloads: {successful_downloads}")
    print(f"  Total Failed Downloads: {failed_downloads}")
    print(f"{Fore.CYAN}Download process completed.")

if __name__ == "__main__":
    main()
