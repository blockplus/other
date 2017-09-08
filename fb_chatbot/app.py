from flask import Flask, request, abort
import requests
import logging

# Set up global variables here, will be stored as env variables in prod

# Set the path to you ssl certificates, needed as FB requires HTTPS webhooks
SSL_CERTIFICATE = \
    '/home/abhishekram/certificates/abhishekram.hopto.org/fullchain1.pem'
SSL_PRIVATE_KEY = \
    '/home/abhishekram/certificates/abhishekram.hopto.org/privkey1.pem'

# Enter the Page and webhook tokens
FB_PAGE_TOKEN = 'EAATZCJwvx3ksBAEG1ZBDkUqrf238XpwWRd4o29pi6l2qyl0ODxuZBqS' \
                'U9aok4l0xj7MOwdOK7Wn3vyupo0axoSavF1CMwLNZBRZBWVYfvLonm8c' \
                'hW8ZCGDY9hVU1laWpjGXniwlGVcugrpQyTrLzuBYZCni7aAlsGPnTFtB' \
                'B0WpitxCZAyNNybgy'
FB_WEBHOOK_TOKEN = 'PtvFy6W4keqfssZ8SdAxEKvxVm6FAX'

# Set up the flask application
app = Flask(__name__)


# Define the endpoint for receiving webhook requests from FB
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # If method is GET and mode is subscribe then verify token and
    # return the challenge to complete verification on developer site
    if request.method == 'GET':
        if request.args['hub.mode'] == 'subscribe' \
                and request.args['hub.verify_token'] == FB_WEBHOOK_TOKEN:
            app.logger.info('Validating the webhook')
            return str(request.args['hub.challenge'])
        else:
            app.logger.error(
                'Failed validation. Make sure the validation tokens match.')
            abort(403, message='Validation Failed')
    else:
        app.logger.debug('Received a post request with body %s' % request.json)
        # For all page requests, loop through each message in each entry
        if request.json['object'] == 'page':
            for entry in request.json['entry']:
                for msg in entry['messaging']:
                    if msg.get('postback'):
                        # If postback is received i.e. user clicks Get Started
                        # button, respond the the user
                        app.logger.info(
                            'User %s has started a conversation' %
                            msg['sender']['id'])

                        # Get sender details from the Graph API
                        user_info = requests.get(
                            'https://graph.facebook.com/v2.6/%s' %
                            msg['sender']['id'],
                            params={'access_token': FB_PAGE_TOKEN}).json()

                        # Respond back to the user with the welcome message
                        welcome_message = {
                            'recipient': {
                                'id': msg['sender']['id']
                            },
                            'message': {
                                'text': 'Hi {}, nice to meet you'.format(
                                    user_info['first_name'])
                            }
                        }
                        send_message = requests.post(
                            'https://graph.facebook.com/v2.6/me/messages',
                            params={'access_token': FB_PAGE_TOKEN},
                            json=welcome_message)
                        app.logger.info(
                            'Sent message response %s' % send_message.text)

                    elif msg.get('message'):
                        # TODO: Add relevant logic to respond to message
                        app.logger.info(
                            'Received a new message from %s with '
                            'contents %s' % (msg['sender']['id'],
                                             msg['message']['text']))
        return 'OK', 200


if __name__ == '__main__':
    handler = logging.StreamHandler()
    log_format = logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(log_format)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.run('0.0.0.0', ssl_context=(SSL_CERTIFICATE, SSL_PRIVATE_KEY))
