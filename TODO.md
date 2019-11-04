# A TODO List!

## Required Functionality

### Encapsulate Model

* Use a docker volume to specify the location of the model parameters
  * Can just use `docker cp /some/file <container-id>:/some/path`
  * Just need to define a specifc file hierarchy where things are expected in the
    container
  * Possibly the ideal approach is for the concrete Figmentator class code to be in a
    directory along with the model parameters. Then the Figmentator can load the
    parameters by simply finding the model parameters in the same folder as the
    Figmentator
* Should create an example Figmentator. It should:
  * require pytorch
  * load a fake set of parameters
  * inference should consistent of just adding some portion of "lorem ipsum" to the
    scene entry's description based upon the passed in range

## Advanced Functionality

* Support HTTPS and/or HMAC authentication to use the API


## Documentation

* Write basic README.md to document how to use this repo, so you do not forget
  important processes or commands
* Create an interactive documentation website using mkdocs and the material
  theme
