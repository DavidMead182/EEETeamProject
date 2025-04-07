def convert_txt_to_string_format(input_file, output_file):
    with open(input_file, 'r') as infile:
        # Read each line (JSON object)
        lines = infile.readlines()

    # Prepare the data by converting each line to the desired format
    formatted_lines = []
    for line in lines:
        # Strip any extra spaces/newlines
        json_obj = line.strip()
        # Escape the quotes and backslashes correctly
        escaped_json = json_obj.replace('"', '\\"')
        formatted_lines.append(f'"{escaped_json}",')  # Add comma at the end of each line

    # Join all formatted lines into a single string
    output_data = '\n'.join(formatted_lines)

    # Write the result to the output file
    with open(output_file, 'w') as outfile:
        outfile.write(output_data)

    print(f"Conversion complete. The output has been saved to {output_file}.")

# Usage example
input_file = r'C:\Users\david\Uni\Year 4\TP\EEETeamProject\Team2\tests\input.txt'  # Path to your input text file
output_file = r'C:\Users\david\Uni\Year 4\TP\EEETeamProject\Team2\tests\output.txt'  # Path to your desired output text file
convert_txt_to_string_format(input_file, output_file)
