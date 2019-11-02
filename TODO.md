# A TODO List!

## Required Functionality

### Encapsulate Model

* In order to make preprocessing and suggestion generation modular need define
  an abstract class to encapsulate a model
* The base class should define these abstract methods:
  * Startup/shutdown (basically should load/unload the model)
  * Preprocess (and possibly cache)
  * Generate (takes in a dict in a specific format... might use pydantic to
    verify)

### Story Processing/Running summarization

* Use aiocache to preprocess and cache off data needed for generation
* Use with Redis for real deployment, or just in memory for dev

### Generating suggestions

* Create a publisher/consumer model to generate suggestions.
  * Web service publishes generation request to the queue and receives an event
    to wait on
  * Create a single consumer that is a periodic polling task that selects up to
    `max_batch_size` number of suggestion requests to complete
    * The consumer runs the task in an executor (either Threaded or Process
      based) in order to ensure it happens in parallel
    * After executor completes it signals the events associated with requests
      in that batch


## Advanced Functionality

* Support HTTPS and/or HMAC authentication to use the API


## Documentation

* Write basic README.md to document how to use this repo, so you do not forget
  important processes or commands
* Create an interactive documentation website using mkdocs and the material
  theme
