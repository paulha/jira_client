import os
import logging
import logging.config
import yaml

"""
Get configuration from yaml file.  Sets up logging streams as defined in logger.yaml.

Returned values:

root    -   Root logger stream. Standard log stream sent to console and output file.
console -   Logs only to the console
logger  -   For convenience, this is the same as the root stream.

A particular output stream can be gotten by Logger.getLogger("<name>"), where <name>
is the definition of the stream from the YAML file. If it happens that <name> is not
defined in the file, it seems to default to the root stream.
"""

def setup_logging(
    default_path='logging.yaml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

# -- Don't need to do configuration more than once...
try:
    logger
except:
    setup_logging()
    logger =logging.getLogger("root")
    root =logging.getLogger("root")
    console = logging.getLogger("console")

"""
root.fatal("FATAL to root -- This should go to everyone...")
root.error("Error to root -- This should go to everyone...")
root.warning("Warning to root -- This should go to everyone...")
root.info("Info to root -- This should go to everyone...")
root.debug("debug level to root")

console.fatal("FATAL to my_module -- This should go to everyone...")
console.error("Error to my_module -- This should go to everyone...")
console.warning("Warning to my_module -- This should go to everyone...")
console.info("Info to my_module -- This should go to everyone...")
console.debug("debug level to my_module")

undefined = logging.getLogger("undefined")
undefined.fatal("FATAL to xyzzy -- This is an undefined logger...")
undefined.error("Error to xyzzy -- This is an undefined logger...")
undefined.warning("Warning to xyzzy -- This is an undefined logger...")
undefined.info("Info to xyzzy -- This is an undefined logger...")
undefined.debug("Debug level to xyzzy -- This is an undefined logger...")

"""

