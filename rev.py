import subprocess
import time
import random
import os

# Finest chatGPT code

cookies_directory = r"C:/chat/clewd/cookies"  # Path to the directory containing the cookie text files

cookie_files = os.listdir(cookies_directory)
shuffled_cookie_files = cookie_files.copy()
random.shuffle(shuffled_cookie_files)

def run_clewd():
    cmd_start = [
        "node", "clewd.js",
    ]

    # Run clewd.js in the background as a subprocess
    clewd_process = subprocess.Popen(cmd_start, cwd=r"C:/chat/clewd", stdout=subprocess.PIPE, universal_newlines=True)
    
    count_200 = 0
    error_found = False
    capabilities_found = False
    
    start_time = time.time()  # Record the start time
    
    while not (count_200 >= 5 or error_found):
        output_line = clewd_process.stdout.readline()
        print(output_line, end='')  # Print the subprocess output
        
        if "200!" in output_line:
            count_200 += 1
        
        if "Error" in output_line:
            error_found = True
        
        if "capabilities" in output_line:
            capabilities_found = True
        
        if not capabilities_found and time.time() - start_time > 3:
            break

    # Terminate the clewd.js process
    print("count: ", count_200, "error found: ", error_found, "capabilities found: ", capabilities_found, "time elapes: ", time.time()- start_time)
    clewd_process.terminate()
    clewd_process.wait()


def update_cookie_in_config(cookie_filename):
    # Read the content of the cookie file
    with open(cookie_filename, 'r') as cookie_file:
        cookie_value = cookie_file.read().strip()

    # Read the content of config.js
    with open('config.js', 'r') as config_file:
        config_content = config_file.read()

    # Find the "Cookie" line and update its value
    updated_config_content = []
    for line in config_content.split('\n'):
        if '"Cookie":' in line:
            updated_config_content.append(f'    "Cookie": "{cookie_value}",')
        else:
            updated_config_content.append(line)

    # Write the updated content back to config.js
    with open('config.js', 'w') as config_file:
        config_file.write('\n'.join(updated_config_content))


while True:
    for selected_cookie_file in shuffled_cookie_files:
        cookie_filename = os.path.join(cookies_directory, selected_cookie_file)
        
        update_cookie_in_config(cookie_filename)
        print("updating cookie in config...")
        time.sleep(1)
        run_clewd()
        time.sleep(2.4)

    # If all cookie files used, reshuffle and repeat
    random.shuffle(shuffled_cookie_files)
