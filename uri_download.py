#!/usr/bin/env python3

"""
Login to the URI Online Judge website, extracts the user's first accepted submissions
and download them.
"""

import os
import time
import getpass

import mechanicalsoup


class URISubmissionDownload():
    """Allows that users submissions on URI-Online-Judge be downloaded automatically."""

    def __init__(self):
        self.email = None
        self.password = None
        self.browser = None
        self.submissions = {}

    @staticmethod
    def get_file_extension(language):
        """
        Retrieve a file extension based on the abbreviation received.

        Args:
            language (str): Abbreviation used by URI for the language.

        Returns:
            str: extension for the file.
        """

        extension = {
            "c++17": "cpp",
            "c++": "cpp",
            "c99": "c",
            "c": "c",
            "python2": "py",
            "python3": "py",
            "go": "go",
            "postgresql": "sql",
            "c#": "cs",
            "haskell": "hs",
            "java": "java",
            "javascript": "js",
            "kotlin": "kt",
            "lua": "lua",
            "ocaml": "ml",
            "pascal": "pas",
            "ruby": "rb",
            "scala": "scala",
        }
        return extension.get(language, "txt")

    def get_login_info(self):
        """Prompt the user for their user and password."""
        self.email = input("Email: ")
        self.password = getpass.getpass()

    def uri_login(self):
        """
        Login in the URI website using MechanicalSoup module
        and creates a StatefullBrowser instance.
        """
        self.get_login_info()

        browser = mechanicalsoup.StatefulBrowser()
        browser.open("https://www.urionlinejudge.com.br/judge/pt/login")

        browser.select_form('form[action="/judge/pt/login"]')
        browser["email"] = self.email
        browser["password"] = self.password
        browser.submit_selected()

        # Check if the dashboard element exists
        login_status = browser.get_current_page().find("div", class_="pn-dashboard")
        if login_status is None:
            print("Failed to login! Check your credentials.")
            return

        self.browser = browser

    def is_logged(self):
        """Check if a browser instace exists."""
        if self.browser is None:
            return False
        return True

    def uri_logout(self):
        """Destroy the StatefulBrowser instance"""
        if self.browser is not None:
            self.browser.close()
            self.browser = None

    def extract_submissions(self):
        """
        Scrapes the submissions from the URI website and
        creates a StatefulBrowser instance.

        *Adds only the first submission that was accepted*.
        """
        if not self.is_logged():
            return

        page = 1
        is_last_page = False
        base_url = "https://www.urionlinejudge.com.br"
        while not is_last_page:
            print(f"Extracting submissions from page: {page}...")
            self.browser.open(
                f"{base_url}/judge/pt/runs?page={page}")

            # Add all submissions on current page
            page_submissions = []
            for row_class in ["par", "impar"]:
                page_submissions += self.browser.get_current_page().find_all("tr", class_=row_class)

            # Extract data from each submission
            for sub in page_submissions:
                if sub is not None and sub.text.strip() != "":
                    submission_info = sub.find_all("td")
                    status = submission_info[4].text.strip().lower()
                    if status == "accepted":
                        problem_number = submission_info[2].text.strip()
                        language = submission_info[5].text.strip().replace(
                            " ", "").lower()
                        submission_url = submission_info[0].find(
                            "a").get("href")
                        problem_url = submission_info[2].find("a").get("href")
                        self.submissions[problem_number] = {
                            "language": language,
                            "problem_url": base_url + problem_url,
                            "submission_url": base_url + submission_url
                        }
            page += 1

            # Check if next page button is disabled
            next_page_button = self.browser.get_current_page().find("li", class_="next")
            is_last_page = "disabled" in next_page_button.get("class")

            time.sleep(5)

    def extract_problem_category(self, url):
        self.browser.open(url)
        html = self.browser.get_current_page()
        if 'a url solicitada não foi encontrada neste servidor' in html.text.lower():
            return ''
        # Extracts the category of the question
        category = html.find(
            "div", class_="tour-step-problem-menu").find('ul').find('li')
        category = category.text.strip().title()
        return category

    def extract_submission_code(self, url):
        self.browser.open(url)
        # Extracts the code of the submission
        html = self.browser.get_current_page()
        code = html.find("pre").text
        return code

    def download_submissions(self):
        """Extract the code from submissions from the URI website and save them to files."""
        if not self.is_logged():
            return

        # Retrieve the user's submissions
        self.extract_submissions()

        download_dir = "URI-Submissions"
        for problem_number, info in self.submissions.items():
            print(f"Downloading problem {problem_number}...")

            # Extracts the category of the problem
            category = self.extract_problem_category(info['problem_url'])
            category_dir = os.path.join(download_dir, category)
            # Create the category directory if needed
            os.makedirs(category_dir, exist_ok=True)

            # Extracts the code that was submitted
            code = self.extract_submission_code(info["submission_url"])

            # Set the file extension
            extension = self.get_file_extension(info["language"])
            file_path = os.path.join(
                category_dir, f"{problem_number}.{extension}")
            with open(file_path, "w") as code_file:
                code_file.writelines(code)

            time.sleep(5)
        print("Done")


def main():
    """Ask the user for credentials, extract and download submissions."""
    uri_download = URISubmissionDownload()
    uri_download.uri_login()
    uri_download.download_submissions()
    uri_download.uri_logout()


if __name__ == "__main__":
    main()
