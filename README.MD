to run the program:
1. Might need to create a virtual environment
2. create .env file and add a google api key
3. run python main.py  (reading the cv is not integrated into main.py yet)

HOW IT WORKS FOR NOW
- the t2t.lk website is scraped and the data is saved in t2t_knowledge.txt in the format
-- Date:
-- ==WEBSITE DATA ==
-- the data in the website
-- == EVENT DATA ==
-- data in the website about events


- read_cv.py reads a cv thats in the same folder (for now) and reads it and puts the content into a temperory file
- that file is deleted when the user exists that file/ program