import os

# Meanwhile my actually path in folder look like: User\Desktop\...
# But, the Practical telling to find '/', so the path look like: User/Desktop/...
# If '\' then '/' -> '\\'

def count_slashes(path):
    # Count the number of '/' characters in a given file path.
    return path.count('/')

def count_components(path):
    # Count the number of components in a given file path.    
    # Split the path by '/' and remove empty components
    components = path.strip().split('/')
    # Remove empty components caused by leading'/'trailing slashes
    components = [x for x in components if x]
    return len(components)

def find_longest_paths(input_files):
    # Find the file path(s) with the most '/' characters across multiple input files.
    # Parameters:
    #     input_files (list): List of input file paths.
    # Returns:
    #     longest_paths (list): List of longest paths (by slash count).
    #     max_slash_count (int): Number of '/' characters in the longest path(s).
    #     max_component_count (int): Number of component(s) in the longest path(s).

    longest_paths = []
    max_slash_count = 0
    max_component_count = 0

    for file in input_files:
        print(f"Processing file: {file}")
        try:
            with open(file, 'r') as f:
                for line in f:
                    path = line.strip()
                    slash_count = count_slashes(path)
                    component_count = count_components(path)

                    if slash_count > max_slash_count:
                        max_slash_count = slash_count
                        longest_paths = [path]
                    elif slash_count == max_slash_count:
                        longest_paths.append(path)

                    if component_count > max_component_count:
                        max_component_count = component_count
                        longest_paths = [path]

        except FileNotFoundError:
            print(f"Error: File '{file}' not found.")

        except Exception as e:
            print(f"An error occurred while processing '{file}': {e}")

    return longest_paths, max_slash_count, max_component_count

def main():
    # List of input files contain file's paths
    input_files = ["laptop1.txt", "laptop2.txt", "laptop3.txt"]

    longest_paths, max_slash_count, max_component_count = find_longest_paths(input_files)

    print("\n=== Longest File Path ===")
    for path in longest_paths:
        print(f"Path: {path}")
    print(f"\nNumber of '/' in the longest path(s): {max_slash_count}")
    print(f"\nNumber of component(s) in the longest path(s): {max_component_count}")

if __name__ == "__main__":
    main()
