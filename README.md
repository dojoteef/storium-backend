<div align="center">
  <img src="https://storium.cs.umass.edu/static/figment.svg">
</div>

# Storium Backend Web Service

This is the official repository of the [backend web
service](https://storium.cs.umass.edu) for the EMNLP 2020 long paper *[STORIUM:
A Dataset and Evaluation Platform for Machine-in-the-Loop Story
Generation](https://arxiv.org/abs/2010.01717)*.

## Python Package Naming

You might ask yourself, what is a figmentator? A figmentator generates figments
of the imagination. In the context of this code, it represents a story
generation model. Why the weird name? Well it's distinctive and I was already
[woolgathering](https://github.com/dojoteef/storium-frontend)...


## Usage

There are are currently three environments: dev, stage, & prod. Run `make
build-dev` or `make build-prod` to create the docker containers to deploy the
service.

Afterward you can run `deploy-dev` or `make deploy-prod` to start the service.


# Deployment

Our [evaluation platform](https://storium.cs.umass.edu) is designed to make it
easy to deploy your story generation models, requiring the implementation of a
simple API to facilitate hosting. You can see a contrived example in
[src/figmentator/examples/simple.py](src/figmentator/examples/simple.py), or a
real example from our [GPT-2
models](https://github.com/dojoteef/storium-gpt2#deployment].
