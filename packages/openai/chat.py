#--web true
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
import re
import requests

ROLE = """
When requested to write code, pick Python.
When requested to show chess position, always use the FEN notation.
When showing HTML, always include what is in the body tag, 
but exclude the code surrounding the actual content. 
So exclude always BODY, HEAD and HTML .
"""

MODEL = "gpt-35-turbo"
AI = None

def req(msg):
    return [{"role": "system", "content": ROLE}, 
            {"role": "user", "content": msg}]

def ask(input):
    comp = AI.chat.completions.create(model=MODEL, messages=req(input))
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"


"""
import re
from pathlib import Path
text = Path("util/test/chess.txt").read_text()
text = Path("util/test/html.txt").read_text()
text = Path("util/test/code.txt").read_text()
"""
def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    return res

def get_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        # I get only the first email address
        return emails[0]
    return None

def notify_slack(payload, slack_url):
    print("Sending Slack notification...")
    response = requests.post(slack_url, json=payload, headers={'Content-type': 'application/json'})
    print(f"Slack notification response: {response.text}")

def handle_email(text, slack_url):
    email = get_email(text)
    if email:
        payload = {"text": f"New email detected: {email}"}
        notify_slack(payload, slack_url)

def main(args):
    global AI
    (key, host, slack_url) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"], args["SLACK_URL"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)

    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Welcome to the OpenAI demo chat",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        output = ask(input)
        res = extract(output)
        handle_email(input, slack_url)
        res['output'] = output

    return {"body": res }
