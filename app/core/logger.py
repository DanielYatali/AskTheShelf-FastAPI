import logging
# Configure basic logging
# Configure basic logging with line number
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - [%(lineno)d] - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)

