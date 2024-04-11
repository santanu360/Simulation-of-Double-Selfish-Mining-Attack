import string
import random
import os


def generate_random_id(length=4):
    # Define the characters to choose from
    characters = (
        string.ascii_uppercase + string.digits
    )  # You can customize this as needed

    # Generate a random 4-character ID
    random_id = "".join(random.choice(characters) for _ in range(length))

    return random_id


def expon_distribution(mean: float):
    """
    Generate a random number from exponential distribution with given mean
    """
    sample = random.expovariate(1 / mean)
    return round(sample, 6)


def create_directory(directory_path):
    """
    Create a directory if it does not exist.
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
        except OSError as e:
            print("unable to create path", e)


def change_directory(directory_path):
    """
    Change the current working directory to the specified path.
    """
    try:
        os.chdir(directory_path)
    except OSError as e:
        print("unable to change directory", e)


def copy_to_directory(src, dst):
    """
    Copy a file from src to dst.
    """
    try:
        os.system(f"cp -r {src} {dst}")
    except OSError as e:
        print("unable to copy", e)


def clear_dir(dir):
    """
    Clear the graph directory.
    """
    try:
        os.system(f"rm -r {dir}/*")
    except OSError as e:
        print("unable to clear graph directory", e)


def delete_pattern(pattern):
    """
    Delete files matching the pattern.
    """
    try:
        os.system(f"rm -rf {pattern}")
    except OSError as e:
        print("unable to clear graph directory", e)
