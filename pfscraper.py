# PFSCRAPER 1.0.1
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as Soup
from datetime import datetime
import csv, time, sys

# SETTINGS AND VARIABLES -------------------------------------------------------
# INFO: I MOVED THE USERNAME AND PASSWORD TO THE key.txt file, please edit it !!
# PF will most likely ask for 2-Factor Authentication on First Run -------------
f = open('key.txt', 'r', encoding='utf-8')
r = csv.reader(f)
try:
    username, password = next(r)
except:
    pass
if username is None or password is None:
    input('CRITICAL ERROR!!! PLEASE SUPPLY key.txt file containing username and password...')
    sys.exit()
# Timings
timeoutFactor = 1.0   # If error eccurs during bad internet, change this to a higher value instead of the 2 values below
timeoutShort = 1 * timeoutFactor   # short delay to wait for html elements to load
timeoutSearch = 5 * timeoutFactor  # wait in seconds for search results before begining to parse - low values will cause bugs even on optimal conditions
timeout = 60    # max time to wait for page in case of shitty connection
startTime = time.perf_counter()

# ------------------------------------------------------------------------------
# NO NEED TO CHANGE ANYTHING BELOW - UNLESS PF MAKES MAJOR SITE/LAYOUT UPDATES--
options = webdriver.ChromeOptions()
options.add_argument('user-data-dir=C:/PFSCRAPER/selenium')                     # Hardcoded, no need to change userdir
options.add_experimental_option('excludeSwitches', ['enable-logging'])          # Removes benign error spam in console, don't remove
d = None
wait = None
site = 'https://static.practicefusion.com/apps/ehr/index.html'

# FUNCTION DEFINITIONS ---------------------------------------------------------
def init():
    return webdriver.Chrome(options=options)
def highlight(driver):
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
def parse(driver):
    return Soup(driver.page_source, 'html.parser')
def login():
    d = init()
    wait = WebDriverWait(d,timeout)    
    d.get(site)
    d.find_element(By.CSS_SELECTOR, 'input#inputUsername').click()
    highlight(d)
    d.switch_to.active_element.send_keys(username, Keys.TAB, password, Keys.RETURN)
    return d, wait
def getstamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
    
#  MAIN PROGRAM BODY -----------------------------------------------------------
f = open('input.csv','r',encoding='utf-8')
next(f)
patients = [row.split(', ') for row in f]
d, wait = login()
time.sleep(timeoutShort)
firstRun = False
try:
    warning = d.find_element(By.XPATH,'/html/body/div[2]/div[2]/div/div[3]/div/div/div/div/div[2]/div/div/div[2]/div[9]/div/div/div/p')
    if warning is not None and warning.text == 'Your Login Email or Password is incorrect':
        input('CRITICAL ERROR - Double Check key.txt file for correct username and password! ...Exiting Program...')
        sys.exit()
    if d.find_element(By.CSS_SELECTOR,'button#sendCallButton.btn.btn-primary.btn-login') is not None:
        firstRun = True
except:
    pass
if firstRun:
    input('IMPORTANT!!! PLEASE Authenticate Browser First with 2FA. After that, press ENTER to exit this program...')
    sys.exit()
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'li.charts-updated')))
f = open('output.csv', 'a', encoding='utf-8', newline='')
w = csv.writer(f)
header = ['Count','Name', 'Date of Birth', 'Record Number', 'Status', 'Mobile Number', 'Home Number', 'Work Number', 'Email' , 'Email Reminder', 'Text Reminder', 'Voice Reminder', 'Documentation of Consent', \
    'Address 1', 'Address 2', 'State/ZIP', 'Primary Payer', 'Primary Plan', 'Primary Order of Benefits', 'Primary Insurance ID', 'Secondary Payer', 'Secondary Plan', 'Secondary Order of Benefits', 'Secondary Insurance ID']
w.writerows(([],['Started',getstamp()],header))
f.flush()
records = []
# -------- SEARCH LOOP BODY ----------------------------------------------------
for c, currentPatient in enumerate(patients):
    print('Current Patient:',currentPatient)
    dateStr = currentPatient[2].strip()
    dateObj = datetime.strptime(dateStr, "%m/%d/%Y")
    formattedDate = dateObj.strftime("%b %d, %Y")
    searchString = currentPatient[0] + ', ' + currentPatient[1] + ' - ' + formattedDate
    lastname = currentPatient[0].lower()
    firstname = currentPatient[1].lower()
    birthdate = formattedDate
    print('Lastname -> ', lastname)
    print('Firstname ->', firstname)
    print('Date of Birth ->', birthdate)
    d.find_element(By.CSS_SELECTOR,'li.charts-updated').click()
    time.sleep(timeoutSearch)
    wait.until(EC.presence_of_element_located((By.TAG_NAME,'input')))
    search = d.find_element(By.XPATH,'/html/body/div[2]/div[2]/div[4]/div/div[2]/div/section/div/div/div/div/div[4]/div/div/div[1]/div/ul/li/input')
    try:
        d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div/section/div/div/div/div/div[4]/div/div/div[1]/div/ul/li[1]/div/div/div/i').click()
    except:
        pass
    print(f'Searching for "{lastname}"')
    search.send_keys(lastname); time.sleep(timeoutShort); search.send_keys(Keys.RETURN)
    time.sleep(timeoutSearch)
    soup = parse(d)
    wait.until(EC.visibility_of_element_located((By.TAG_NAME,'tbody')))
   
    rows = soup.find_all('tr')
    found = False

    for i, row in enumerate(rows):
        firstnameDiv = row.find('div', {'data-element': 'patient-first-name'})
        lastnameDiv = row.find('div', {'data-element': 'patient-last-name'})
        birthdateDiv = row.find('div', {'class': 'hidden-xs hidden-sm'})
        
        if (firstnameDiv and firstnameDiv.text.strip().lower() == firstname) and \
        (lastnameDiv and lastnameDiv.text.strip().lower() == lastname) and \
        (birthdateDiv and birthdateDiv.text == birthdate):
            print(f"MATCHING RECORD FOUND! --> {searchString}")
            print('ROW #: ',i)
            found = i
            break
    if not found:
        print(f'SEARCH FAILED!!! NO MATCHING RECORD FOUND FOR: {searchString}')
        continue
    table = d.find_element(By.CSS_SELECTOR,'tbody')
    target = table.find_elements(By.TAG_NAME, 'tr')[found-1]
    target.click()
    print(f'Reading Records of Patient: {searchString}...')
    time.sleep(timeoutSearch)
    d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[1]/ul/li[4]').click()
    time.sleep(timeoutSearch)
    # -------- RECORD BODY -----------------------------------------------------
    soup = parse(d)
    name, dob, recordNumber, status, mobileNumber, homeNumber, workNumber, email, emailReminder, textReminder, voiceReminder, consent, address1, address2, state, payer1, plan1, order1, insuranceID1, payer2, plan2, order2, insuranceID2 = (None,) * 23
    try:
        print('GRABBING DATA...')
        # I know full XPATH is ugly to look at but this is definitely the only reliable way to pinpoint these elements on this particularly tricky site
        name = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/p[1]').text
        dob = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/p[7]').text
        recordNumber = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/p[2]').text
        status = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div/div[2]/div[2]/div/div/div[2]/p[3]').text
        mobileNumber = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[1]/div[1]/div/div/div[2]/p[2]').text
        homeNumber = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[1]/div[1]/div/div/div[2]/p[3]').text
        workNumber = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[1]/div[1]/div/div/div[2]/p[4]').text
        email = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[1]/div[2]/div/p[1]').text
        address1 = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[4]/div[1]/div[2]/div/div/div/button/div[3]/div[1]/p[1]').text
        address2 = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[4]/div[1]/div[2]/div/div/div/button/div[3]/div[1]/p[2]').text
        state = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[4]/div[1]/div[2]/div/div/div/button/div[3]/div[1]/p[3]').text
        emailReminder = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/input').get_attribute('checked')
        textReminder = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div[1]/div/div/input').get_attribute('checked')
        voiceReminder = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div[1]/div[1]/div/div/input').get_attribute('checked')
        consent = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[3]/div/div[2]/div[2]/div/div/div/div[4]/div[1]/div[1]').text
        print('DATA COMPLETELY GRABBED ... LIKE A BOSS!')
    except:
        print('PARTIAL DATA GRABBED! - Missing some fields...')
    # -------- INSURANCE BODY --------------------------------------------------
    d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[6]/div/div[2]/div/div/div/ul/li[1]').click()    # Insurance 1
    time.sleep(timeoutShort)
    def getPayer(d):
        return d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[3]/div[2]/div[1]/div/input').get_attribute('value')
    def getPlan(d):
        return d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]/div[1]/input').get_attribute('value')
    def getOrder(d):
        return d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[3]/div[3]/div[1]/div[1]/div/div/button/span').text
    def getInsuranceID(d):
        return d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[3]/div[3]/input[1]').get_attribute('value')
    try:
        payer1 = getPayer(d)
        plan1 = getPlan(d)
        order1 = getOrder(d)
        insuranceID1 = getInsuranceID(d)
    except:
        print('ERROR IN GRABBING PRIMARY INSURANCE INFO!!!')
    time.sleep(timeoutShort)
    try:
        secondaryInsurance = d.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[4]/div/div[2]/div[2]/div/div[1]/div[2]/div[1]/div[3]/div/div[6]/div/div[2]/div/div/div/ul/li[2]')
        if secondaryInsurance:
            secondaryInsurance.click()
        try:
            payer2 = getPayer(d)
            plan2 = getPlan(d)
            order2 = getOrder(d)
            insuranceID2 = getInsuranceID(d)
        except:
            print('ERROR IN GRABBING SECONDARY INSURANCE INFO!!!')
    except:
        pass
    record = (c+1,name, dob, recordNumber, status, mobileNumber, homeNumber, workNumber, email, emailReminder, textReminder, voiceReminder, consent, address1, address2, state, payer1, plan1, order1, insuranceID1, payer2, plan2, order2, insuranceID2)
    print(record)
    records.append(record)
    w.writerow(record)          # moved writing to file here so we have output in case of crash or interruption
    f.flush()                   # force the OS to output to file and not wait for a power outtage ;)
    time.sleep(timeoutSearch)

# END --------------------------------------------------------------------------
duration = time.perf_counter() - startTime
w.writerow(('Completed',getstamp(),'Time Taken', str(int(duration))+' seconds'))
print(f'MISSION ACCOMPLISHED in {duration} seconds!\nSuccessfully processed {len(records)} patient records! ...Exiting app in 5 seconds')
time.sleep(5)
# COPYRIGHT © Alchael 2023 - All Rights Reserved