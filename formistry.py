from aiohttp import web, ClientSession
from aiohttp.web import HTTPFound
from google.cloud import datastore
import json
import urllib
import textwrap
import asyncio
import logging
import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(asctime)s] %(name)s: %(message)s')
slack_hook = "https://hooks.slack.com/services/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"
loop = asyncio.get_event_loop()

async def send_form_to_slack(form, data, headers):
  await send_to_slack({
    "text": "*Formistry submission*",
    "attachments": [
        {
            "pretext": "Form: *{0}*".format(form),
            "fallback": "Form fields",
            "title": "Form fields",
            "color": "good",
            "fields": [
                { "title": field, "value": value} for field, value in data.items()
            ]
        },
        {
            "fallback": "Headers for submission",
            "pretext": "Request headers",
            "fields": [
                { "title": field, "value": value} for field, value in headers.items()
            ]
        }
    ]
  })

async def send_error_to_slack(error):
    await send_to_slack({
        "attachments": [{
            "fallback": error,
            "title": error,
            "color": "danger"
        }]
    })


async def send_to_slack(payload):
  async with ClientSession() as session:
    async with session.post(slack_hook, data=json.dumps(payload)) as resp:
        if resp.status < 200 or resp.status >= 300:
            logging.error("[%s] failure sending to slack: %s", form, resp.status)

async def store_to_datastore(form, data):
    client = datastore.Client(namespace="website_forms")
    entity = datastore.Entity(key=client.key('FormSubmission'))
    entity.update(data)
    entity["Form"] = form
    return loop.run_in_executor(None, client.put, entity)

def write_file(f, data):
    json.dump(data, f)
    f.write("\n")

async def store_to_file(form, data, headers):
    entity = {"date": datetime.datetime.now().isoformat(), "form": form, "data": data, "headers": headers}
    return loop.run_in_executor(None, lambda: write_file(open("/var/formistry/submissions.json", "a+"), entity))

def redirect(referrer, next_url):
    url = urllib.parse.urlparse(referrer)
    redirect_url = urllib.parse.urljoin("{0}://{1}".format(url[0], url[1]), next_url)
    return HTTPFound(redirect_url)

async def handle(request):
    form = request.match_info['form']
    referrer = request.headers["Referer"]
    data = await request.post()
    peername = request.transport.get_extra_info('peername')

    if "_gotcha" in data:
        real_data = dict([(k, v) for k,v in data.items() if k not in ["_next", "_gotcha"]])
        if peername is not None:
            real_data["ip"] = peername[0]
        logging.info("[%s] form submitted with data: %s", form, real_data)
        headers = dict(request.headers)
        await store_to_file(form, real_data, headers)
        await send_to_slack(form, real_data, headers)
        return redirect(referrer, data["_next"])
    else:
        logging.error("[%s] form missing _gotcha: %s", form, data)
        await send_error_to_slack("form missing _gotcha: {0}".format(form))
        return None

app = web.Application()
app.router.add_post('/post/{form}', handle)

web.run_app(app)
