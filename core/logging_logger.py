# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     filename='logging/app.log',
#     filemode='a',
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# def setup_logger(name):
#     logger = logging.getLogger("Chatbot Log")
#     logger.setLevel(logging.INFO)

#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)

#     error_file_handler = logging.FileHandler("logging/error.log")
#     error_file_handler.setLevel(logging.ERROR)

#     console_file_handler = logging.FileHandler("logging/console.log")
#     console_file_handler.setLevel(logging.INFO)

#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     console_handler.setFormatter(formatter)
#     error_file_handler.setFormatter(formatter)
#     console_file_handler.setFormatter(formatter)

#     logger.addHandler(console_handler)  
#     logger.addHandler(error_file_handler)  
#     logger.addHandler(console_file_handler)  

#     return logger

import logging
logging.basicConfig(level=logging.INFO)

def setup_logger(name):
    logger = logging.getLogger("Chatbot Log")
    logger.setLevel(logging.INFO)

    return logger