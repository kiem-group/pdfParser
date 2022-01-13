import logging


def config_logger():
    pipeline_logger = logging.getLogger('pdfParser')
    pipeline_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # create file handler
    fh = logging.FileHandler('pdfParser.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    pipeline_logger.addHandler(fh)
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARN)
    ch.setFormatter(formatter)
    pipeline_logger.addHandler(ch)
    return pipeline_logger