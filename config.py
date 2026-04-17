# This file is to configure the right settings for the SHA Licensed Health Facilities And Funds project

# import necessary modules
import os


class Config:
    # Define the base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'DATA')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'OUTPUT')
    DOCUMENTS_DIR = os.path.join(BASE_DIR, 'DOCUMENTATION')

    os.chdir(BASE_DIR)