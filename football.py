from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
import sys

def sorting_key(match_data):
    total_shots_on_target = match_data['home_shots_on_goal'] + match_data['away_shots_on_goal']
    total_dangerous_attacks = match_data['home_dangerous_attacks'] + match_data['away_dangerous_attacks']
    return total_shots_on_target, total_dangerous_attacks

# Move the definition of match_data_list to here
match_data_list = []

def get_stats_from_driver(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    stats = soup.find_all("div", class_="stat__category")

    # Extract the score
    score_element = soup.find("div", class_="detailScore__wrapper detailScore__live")
    if score_element:
        score = score_element.text.strip()
    else:
        score = "Unknown"

    match_status_element = soup.find("span", class_="fixedHeaderDuel__detailStatus")
    match_status = ""

    if match_status_element:
        match_status = match_status_element.text.strip()

    # Extract the minutes into the game
    match_time_element = soup.find("div", class_="eventAndAddedTime")
    if match_time_element:
        match_time = match_time_element.text.strip()
    else:
        match_time = "Unknown"

    return stats, score, match_status, match_time


def analyze_match(data):
    home_dangerous_attacks = data['home_dangerous_attacks']
    away_dangerous_attacks = data['away_dangerous_attacks']
    home_shots_on_goal = data['home_shots_on_goal']
    away_shots_on_goal = data['away_shots_on_goal']
    home_ball_possession = data['home_ball_possession']
    away_ball_possession = data['away_ball_possession']
    red_cards_found = data['red_cards_found']

    # Define thresholds
    high_ball_possession = 55
    high_attack_efficiency = 0.1
    
    total_dangerous_attacks = home_dangerous_attacks + away_dangerous_attacks
    total_shots_on_goal = home_shots_on_goal + away_shots_on_goal
     # Check if there are any dangerous attacks
    if total_dangerous_attacks == 0:
        return "No dangerous attacks yet; not enough data to analyze."
    # Check if there are any total shots on goal
    if total_shots_on_goal == 0:
        return "No shots on goal yet; highly unlikely anyone will score."

    # Calculate the proportion of dangerous attacks and shots on goal
    home_attack_proportion = home_dangerous_attacks / total_dangerous_attacks
    away_attack_proportion = away_dangerous_attacks / total_dangerous_attacks
    home_shot_proportion = home_shots_on_goal / total_shots_on_goal
    away_shot_proportion = away_shots_on_goal / total_shots_on_goal

    # Calculate attack efficiency
    if home_dangerous_attacks != 0:
        home_attack_efficiency = home_shots_on_goal / home_dangerous_attacks
    else:
        home_attack_efficiency = 0
    
    if away_dangerous_attacks != 0:
        away_attack_efficiency = away_shots_on_goal / away_dangerous_attacks
    else:
        away_attack_efficiency = 0

    # Analyze the data
    analysis = ""
    if red_cards_found == True:
        analysis += "\nRed card found - Ignore match.\n"
    
    if total_dangerous_attacks > 25 or total_shots_on_goal > 3:
        if home_attack_proportion > 0.6 or away_attack_proportion > 0.6:
            analysis += "Higher chance of more goals.\n"
        else:
            analysis += "Match is more balanced; harder to predict more goals.\n"
    else:
        analysis += "Lower chance of more goals.\n"

    analysis += f"Home team's attack efficiency is {home_attack_efficiency:.2f} shots on goal per dangerous attack.\n"
    analysis += f"Away team's attack efficiency is {away_attack_efficiency:.2f} shots on goal per dangerous attack.\n"

    if home_attack_efficiency > away_attack_efficiency:
        analysis += "Home team has a better attack efficiency.\n"
    elif home_attack_efficiency < away_attack_efficiency:
        analysis += "Away team has a better attack efficiency.\n"
    else:
        analysis += "Both teams have similar attack efficiency.\n"

    analysis += f"Home team's ball possession is {home_ball_possession}, while away team's ball possession is {away_ball_possession}.\n"

    if home_ball_possession > away_ball_possession:
        analysis += "Home team has better ball possession.\n"
    elif home_ball_possession < away_ball_possession:
        analysis += "Away team has better ball possession.\n"
    else:
        analysis += "Both teams have equal ball possession.\n"

# Analyze ball possession and attack efficiency
    if home_ball_possession > high_ball_possession and home_attack_efficiency > high_attack_efficiency:
        analysis += "Home team has high ball possession and high attack efficiency, more likely to score. \n"
    elif home_ball_possession < (100 - high_ball_possession) and home_attack_efficiency > high_attack_efficiency:
        analysis += "Home team has low ball possession but high attack efficiency, could be effective at counter-attacking. \n"
    
    if away_ball_possession > high_ball_possession and away_attack_efficiency > high_attack_efficiency:
        analysis += "Away team has high ball possession and high attack efficiency, more likely to score. "
    elif away_ball_possession < (100 - high_ball_possession) and away_attack_efficiency > high_attack_efficiency:
        analysis += "Away team has low ball possession but high attack efficiency, could be effective at counter-attacking. \n"

    return analysis
        
def fetch_stats(match_name, flashscore_link):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36")
    # Replace this with the path to your ChromeDriver
    chromedriver_path = 'C:\chromedriver_win32\chromedriver.exe'
    service = Service(executable_path=chromedriver_path)  # Create a Service object
    driver = webdriver.Chrome(service=service, options=options)  # Pass the Service object to the constructor
    # ... rest of the function
    driver.get(flashscore_link)
    print(f"Fetching stats in function fetch_stats")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".stat__category")))
    except TimeoutException:
        print(f"Match: {match_name}")
        print("Stats data not available. The match may not have started yet.")
        driver.quit()
        return

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    stats = soup.find_all("div", class_="stat__category")
    # Extract the score
    score_element = soup.find("div", class_="detailScore__wrapper detailScore__live")
    if score_element:
        score = score_element.text.strip()
    else:
        score = "Unknown"
        
    match_status_element = soup.find("span", class_="fixedHeaderDuel__detailStatus")
    match_status = ""

    if match_status_element:
        match_status = match_status_element.text.strip()

    if match_status:
        if match_status in ["1st Half", "Half Time"]:
            pass  # Use the existing flashscore_link for the first half
        elif match_status in ["2nd Half", "Finished"]:
            flashscore_link = flashscore_link[:-1] + '2'
            driver.get(flashscore_link)
            stats, score, match_status, match_time = get_stats_from_driver(driver)

        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".stat__category")))
        except TimeoutException:
            print(f"Match: {match_name}")
            print(f"{match_status} stats data not available.")
            driver.quit()
            return
    else:
        print("Match status not found")    
     # Extract the minutes into the game
    match_time_element = soup.find("div", class_="eventAndAddedTime")
    if match_time_element:
        match_time = match_time_element.text.strip()
    else:
        match_time = "Unknown"

    if stats:
        corners_found = False
        fouls_found = False
        dangerous_attacks_found = False
        red_cards_found = False

        for stat_row in stats:
            stat_name = stat_row.find("div", class_="stat__categoryName").text.strip()

            if "Dangerous Attacks" in stat_name:
                dangerous_attacks_found = True
                home_dangerous_attacks = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_dangerous_attacks = stat_row.find("div", class_="stat__awayValue").text.strip()

            if "Corner Kicks" in stat_name:
                corners_found = True
                home_corners = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_corners = stat_row.find("div", class_="stat__awayValue").text.strip()

            if "Fouls" in stat_name:
                fouls_found = True
                home_fouls = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_fouls = stat_row.find("div", class_="stat__awayValue").text.strip()
                 
            if "Red Cards" in stat_name:
                red_cards_found = True
                home_red_cards = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_red_cards = stat_row.find("div", class_="stat__awayValue").text.strip()
                
            if "Ball Possession" in stat_name:
                ball_possesion_found = True
                home_ball_possesion = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_ball_possesion = stat_row.find("div", class_="stat__awayValue").text.strip()    
                
            if "Shots on Goal" in stat_name:
                shots_on_goal_found = True
                home_shots_on_goal = stat_row.find("div", class_="stat__homeValue").text.strip()
                away_shots_on_goal = stat_row.find("div", class_="stat__awayValue").text.strip()                 

        print(f"=========================================================")
        print(f"Match: {match_name}")
        print(f"Half: {match_status}")
        print(f"Minutes into the game: {match_time}")
        print(f"Score: {score}")
        if dangerous_attacks_found:
            print(f"Home Team Dangerous Attacks: {home_dangerous_attacks}")
            print(f"Away Team Dangerous Attacks: {away_dangerous_attacks}")

        if corners_found:
            print(f"Home Team Corners: {home_corners}")
            print(f"Away Team Corners: {away_corners}")

        if fouls_found:
            print(f"Home Team Fouls: {home_fouls}")
            print(f"Away Team Fouls: {away_fouls}")
            
        if red_cards_found:
            print(f"Home Team Red Cards: {home_red_cards}")
            print(f"Away Team Red Cards: {away_red_cards}")

        if ball_possesion_found:
            print(f"Home Team Ball Possesion: {home_ball_possesion}")
            print(f"Away Team Ball Possesion: {away_ball_possesion}")
            
        if shots_on_goal_found:
            print(f"Home Shots on Goal: {home_shots_on_goal}")
            print(f"Away Shots on Goal: {away_shots_on_goal}")            

        print(f"=========================================================")
    
    else:
        print(f"Match: {match_name}")
        print("No stats data found.")
    
    
    match_data = {
    'match_name': match_name,
    'home_dangerous_attacks': int(home_dangerous_attacks),
    'away_dangerous_attacks': int(away_dangerous_attacks),
    'home_shots_on_goal': int(home_shots_on_goal),
    'away_shots_on_goal': int(away_shots_on_goal),
    'home_ball_possession': float(home_ball_possesion[:-1]),
    'away_ball_possession': float(away_ball_possesion[:-1]),
    'match_status': match_status,
    'match_time': match_time,
    'red_cards_found': red_cards_found
    }
    # match_data["match_status"] = match_status
    # match_data["match_time"] = match_time
    print(f"Using flashscore link : {flashscore_link}")
    match_data_list.append(match_data)
    driver.quit()


# Read matches from the text file
if len(sys.argv) > 1:
    input_file_name = sys.argv[1]
else:
    input_file_name = "matches.txt"


matches = []
#global match_data_list
with open(input_file_name, "r") as file:
    for line in file:
        try:
            match_name, flashscore_link = line.strip().split(",")
            flashscore_link = flashscore_link.rstrip('/') + '/match-statistics/1'
            matches.append((match_name, flashscore_link))
        except ValueError:
            print(f"Invalid line format. Skipping line: {line.strip()}")

# Loop through matches and fetch dangerous attacks data
for match_name, flashscore_link in matches:
    print(f"Flashscore link used before pass in: {match_name}{flashscore_link}")
    fetch_stats(match_name, flashscore_link)

sorted_match_data_list = sorted(match_data_list, key=sorting_key)

for match_data in sorted_match_data_list:
    analysis = analyze_match(match_data)
    print(f"{match_data['match_name']}: {analysis}")
    print(f"==================================================================================================================")
