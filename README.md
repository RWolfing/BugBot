# Bugbot - Designing a Chatbot to Elicit Contextual Information of Software Requirements

While user feedback has become a valuable resource to elicit system requirements and identify issues, a common lack of
contextual information in feedback challenges development teams. Previous research has primarily focused on text
analysis through natural language processing to identify topics or trends in user feedback and capture requirements by
summarizing the most common user subjects. However, such approaches fail to improve the general quality of collected
user feedback and the amount of contextual information included. This chatbot prototype uses Rasa Open Source to elicit
contextual information by interacting with users during a conversation.

####Important Note
The chatbot was developed for a german streaming application. Therefore it currently only supports
conversations in german.

## 👷‍ Installation

To install please first install rasa and its dependencies on your system following
the [official documentation](https://rasa.com/docs/rasa/installation/).

The chatbot also uses a knowledge base to infer information using the elastic stack. If you want to use this
functionality you need to run a separate elastic container as described in the [development](#development) section.

## 🤖 How to run

After cloning the repo run Use `rasa train` in the project directory to train a model a new model.

Then to run custom action set up your action server in a separate terminal window running

```bash
rasa run actions --actions actions.actions
```

There are some cusotm actions that require connections to external services specifically `ValidatePlaybackIssueForm`
and `SubmitIncidentAction`. To run these you need to setup your own elastic stack or use a database to connect to. See
the [development](#development) section for more instructions.

To run the Bot use (the debug flag is optional):

```bash
docker run -p 8000:8000 rasa/duckling
rasa shell --debug
```

To run the Bot under http://localhost:5005. Use `html/dev/index.html` for a simple webpage to access the bot.
```bash
rasa run -m models --enable-api --cors "*" --debug
```

## 👩‍💻 Project Structure

`data/stories/` - contains stories

`data/rules/` - contains rules

`data/nlu/` - contains nlu training data

`data/nlu/responses` - contains chatbot responses

`html/dev` - contains a webinterface to interact with the chatbot run http://localhost:5005

`domain.yml` - the domain file, including bot response templates

`config.yml` - training configurations for the NLU pipeline and policy ensemble

`actions` - contains custom action code

## Development

To run custom actions locally, put a file called .env in the root of your local directory with values for the following
environment variables. While the chatbot works generally without them it is recommended to setup up the external
services to see the full functionality.

In our development environment the elastic stack is hidden behind a proxy. To use your own elastic stack either follow
the same approach or review and change `actions/elastic/` to match your requirements. This is WIP.

We save our incident reports using Airtable. To connect to airtable review their documentation
and `actions/util/create_incident_report`. The incident table used needs to include all fields of `create_incident_report`.

```
ELASTIC_HOST=#Domain of the elastic host
ELASTIC_ADMIN=#Elastic login
ELASTIC_PSWD=#Elastic password

AIRTABLE_BASE_ID=#Base ID of your airtable project
AIRTABLE_API_KEY=#API key of your airtable account
AIRTABLE_TABLE=#Table name
```

## Credits

This project is part of my master thesis at the [Universität Hamburg](https://www.uni-hamburg.de/).





