# import sys
#
# from modelmachine import asm
#
#
# def assemble(input_filename: str, output_filename: str) -> int:
#     """Assemble input_filename and wrote output_filename."""
#     with open(input_filename) as input_file:
#         input_data = input_file.read()
#
#     error_list, code = asm.parse(input_data)
#
#     if error_list != []:
#         print("Compilation aborted with errors:")
#         for error in error_list:
#             print(error, file=sys.stderr)
#
#     print("Success compilation.")
#     with open(output_filename, "w") as output_file:
#         print(code, file=output_file)
#     return 0
