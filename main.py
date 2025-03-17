import json
import bs4
from types import NoneType
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class CV_editor:
    """Class that generate the resume."""

    def __init__(self):
        """Load data from JSON files."""
        self.my_data = self.load_json("data/me.json")
        self.certifications = self.load_json("data/certifications.json")
        self.projects = self.load_json("data/projects.json")
        self.titles = self.load_json("data/titles.json")
        self.cv_list = ["ia", "dev"]

    def load_json(self, filename: str) -> dict:
        """
        Load json file.

        :param filename: json filename
        :return: dict withing json file
        """
        with open(filename, encoding="utf-8") as json_file:
            return json.load(json_file)

    def template_choice(self, style: str = "cols") -> str:
        """
        Choose html template based on style.

        :param style: resume style
        :return: template path
        """
        template = f'templates/cv_{style}.html'

        return template

    def cv_selector(self, position: str) -> str:
        """
        Determines the job-related category based on keywords in the input position.

        :param position: job position
        :return: select cv type
        """
        dev = ["developper", "developer", "developpeur", 'back-end', "back end"]
        ia = ["science", "scientist", " ai", ' ia', "ai ", "ia ", 'machine learning', "deep learning", "data"]

        if True in [x in position for x in ia]:
            cv = "ia"
        elif True in [x in position for x in dev]:
            cv = "dev"
        else:
            raise Exception("No resume available")

        return cv

    def fill_tag(self, soup: bs4.BeautifulSoup, element: bs4.element.Tag, element_id: str, value: str,
                 lang: str) -> bs4.BeautifulSoup:
        """
        Fill resume based on given data.

        :param soup: hmtl code
        :param element: html tag
        :param element_id: cv htlm tag id
        :param value: value to fill with
        :param lang: language to use
        :return: filled tag in html format
        """
        if isinstance(value, list):
            ul = soup.new_tag("ul", **{"class": "missions"})
            for val in value:
                li = soup.new_tag("li", **{"class": "missions"})
                li.string = val
                ul.append(li)
            element.append(ul)

        else:
            element.string = value if "linkedin" not in value else "linkedin: ThomasBoulanger"

        # if project element add project description
        if "project" in element_id:
            element = soup.find(id="project_description" + ''.join(i for i in element_id if i.isdigit()))
            element.string = self.projects[lang][value]

        # if certifications element add certification link
        elif "certif" in element_id:
            element["href"] = self.certifications[value]

        # if link element add link
        elif "link_" in element_id:
            element["href"] = value

        return soup

    def fill_resume(self, position: str, company: str, lang: str, cv: str, style: str) -> str:
        """
        Fill resume based on given data.

        :param position: job's position
        :param company: job's company
        :param lang: cv language
        :param cv: resume category to choose
        :param style: css file to choose
        :return: filled resume in html format
        """
        data = self.my_data
        data = {key: value for key, value in data[lang].items() if key not in self.cv_list} | data[lang][cv] | {
            "company": company.upper(), "position": position.upper()} | self.titles[lang]

        # Load the HTML template
        templates = self.template_choice(style)
        with open(templates, 'r', encoding="utf-8") as html_file:
            soup = BeautifulSoup(html_file, 'html.parser')

            for element_id, value in data.items():
                element = soup.find(id=element_id)
                if not isinstance(element, NoneType):
                    soup = self.fill_tag(soup, element, element_id, value, lang)

        return soup.prettify()

    def save_html(self, html: str) -> None:
        """
        Save html file.

        :param html: string html to save
        :return:
        """
        with open('templates/prov.html', 'w', encoding='utf-8') as file:
            file.write(html)

    def generate_pdf(self, html_file: str, output_path: str) -> None:
        """
        Generate pdf based on html file.

        :param html_file: html file path to consider
        :param output_path: resume output path
        :return:
        """
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f'file:///{html_file}')
            page.pdf(path=output_path, print_background=True, width="210mm", height="297mm")
            browser.close()

    def run(self, position: str, company: str, lang: str = "fr", style: str = "cols") -> None:
        """
        Run resume generato pipeline.

        :param position: job position
        :param company: job company
        :param lang: resume language
        :param style: resume's template name
        :return:
        """
        cv = self.cv_selector(position)
        html = self.fill_resume(position, company, lang, cv, style)
        self.save_html(html)
        self.generate_pdf("templates/prov.html", 'cv_lm/cv.pdf')


if __name__ == '__main__':
    cv_gen = CV_editor()
    cv_gen.run("data guy", "fancy company name in Barcelona", lang="fr", style="cols")
