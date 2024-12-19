import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
from IPython.display import Markdown, display, update_display
import streamlit as st


load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")

MODEL = 'gpt-4o-mini'  # Adjust the model as needed

openai = OpenAI()

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    """
    A utility class to represent a Website that we have scraped, now with links
    """

    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

link_system_prompt = (
    "You are provided with a list of links found on a webpage. "
    "You are able to decide which of the links would be most relevant to include in a brochure about the company, "
    "such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
    "You should respond in JSON as in this example:\n"
    "{\n"
    '    "links": [\n'
    '        {"type": "about page", "url": "https://full.url/goes/here/about"},\n'
    '        {"type": "careers page", "url": "https://another.full.url/careers"}\n'
    "    ]\n"
    "}"
)

def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. "
    user_prompt += "Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

def get_all_details(url):
    result = "Landing page:\n"
    landing = Website(url)
    result += landing.get_contents()
    links = get_links(url)
    for link in links["links"]:
        w = Website(link["url"])
        result += f"\n\n{link['type'].capitalize()}\n"
        result += w.get_contents()
    return result

def get_brochure_user_prompt(company_name, url):
    """
    Build a user prompt that contains the relevant content from the company's website.
    """
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += get_all_details(url)
    # Truncate if too long
    user_prompt = user_prompt[:5000]
    return user_prompt

def multi_lingual_stream_brochure(company_name, url, language, tone):
    """
    Generate a multilingual brochure with a given tone using the OpenAI streaming API.
    """

    # System prompt with placeholders for language and tone
    system_prompt = f"""
You are an assistant that analyzes the contents of several relevant pages from a company website and creates a visually appealing and professional short brochure for prospective customers, investors, and recruits. 
The brochure should be written in {language} and use a {tone.lower()} tone throughout.

The brochure should follow this structure (in {language}):

1. **Front Cover**:
   - Prominently display the company name as Title.
   - Include a compelling headline or tagline.
   - Add something engaging relevant to the company’s mission.

2. **About Us**:
   - Provide a brief introduction to the company.
   - State the company’s core mission and vision.
   - Mention the founding story or key milestones.

3. **What We Offer**:
   - Summarize the company's products, services, or solutions.
   - Highlight benefits or unique selling points.
   - Include testimonials or case studies if available.

4. **Our Culture**:
   - Outline the company’s key values or guiding principles.
   - Describe the workplace environment (e.g., innovation-driven, inclusive, collaborative).
   - Highlight community engagement or CSR initiatives.

5. **Who We Serve**:
   - Describe the target customers or industries served.
   - Mention notable clients or partners.
   - Include testimonials or endorsements from customers.

6. **Join Us**:
   - Detail career or internship opportunities.
   - Highlight benefits, career growth, or training opportunities.
   - Provide direct links or steps to apply.

7. **Contact Us**:
   - Provide the company’s address, phone number, and email.
   - Include links to social media platforms.
   - Add a link to the company’s website.

8. **Closing Note**:
   - End with a thank-you message or an inspirational note for the reader.
   - Add a call-to-action (e.g., “Get in touch today!” or “Explore more on our website”).

Ensure the content is concise, engaging, visually clear, and tailored to the target audience. Use headings and subheadings to make the brochure easy to navigate. Include links and contact information wherever applicable.
"""

    stream = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
          ],
        stream=True
    )
    
    # response = ""
    # display_handle = display(Markdown(""), display_id=True)
    # for chunk in stream:
    #     response += chunk.choices[0].delta.content or ''
    #     response = response.replace("```","").replace("markdown", "")
    #     update_display(Markdown(response), display_id=display_handle.display_id)

    response = ""
    placeholder = st.empty()  # Create a placeholder for dynamic updates

    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        response = response.replace("```", "").replace("markdown", "")
        placeholder.markdown(response)  # Update the placeholder dynamically
