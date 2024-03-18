################################################################################
# Copyright 2023 E. Kooistra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
# Author: Eric Kooistra.
# Date: 5 jan 2024
"""Module to use and evaluate parameters sections in a CSV file

A parameters section contains one or more parameters. There can be multiple
parameters section. A parameter consists of a name, expression pair. The
expression of a parameter can use preceding parameters. The expression can use
the functions from math.

Inside the parameters sections parameter names of preceding parameters can be
used in expressions for new parameters. The expression is evaluated to set
the new parameter value.

Outside the parameters sections parameter names can be used with a preceding $.
The $parameter names will be replaced by their value and if they are part of
an expression, then the expression is evaluated to set the value.

Inside the parameters sections only preceeding parameter names can be used,
outside the parameter sections parameters can be used anywhere in the file,
so also before they are defined.

The start of one parameter name must not be identical to another parameter
name, to avoid partial parameter name substitution.

Based on safe eval() code from:
. https://realpython.com/python-eval-function/#restricting-the-use-of-built-in-names
. https://lybniz2.sourceforge.net/safeeval.html
"""

import re
import math
import interfacefiles


# Dict of math functions for eval()
_mathDict = {k: v for k, v in math.__dict__.items() if not k.startswith('__')}


def read_parameters_from_file_lines(fileLines):
    """Read parameters sections from fileLines of file.

    parameters
      p0, expression0
      p1, expression1
      .., ...
      pN, expressionN

    Input:
    . fileLines: read lines from comma separate values file
    Return:
    . parametersDict: dictionary of parameter name and expression result
      pairs if parameters are valid, else empty dictionary.
    """
    emptyDict = {}
    parametersDict = {}
    nofParameters = 0
    readParameters = False
    for li, fLine in enumerate(fileLines):
        entries = interfacefiles.get_file_line_entries(fLine)
        lineWord = entries[0]
        if lineWord == '':
            # End of any section
            readParameters = False
        elif lineWord == 'parameters':
            # Start of parameters section
            readParameters = True
        elif readParameters:
            # Check entries is a pair
            if len(entries) != 2:
                print('ERROR line %d: Not a parameter, expression pair %s' % (li, str(entries)))
                return emptyDict
            name = entries[0]
            expressionStr = entries[1]
            # Validate parameter name
            parameterMsg = _validate_parameter_name_in_dict(name, parametersDict)
            if parameterMsg:
                print('ERROR line %d: %s' % (li, parameterMsg))
                return emptyDict
            # Parse parameter expression for existing parameters
            expressionMath = _parse_parameter_expression(expressionStr, parametersDict)
            # Evaluate parameter expression
            # print('expressionMath = %s' % str(expressionMath))
            value = _eval_expression(expressionMath)
            # Add parameter
            parametersDict[name] = value
            nofParameters += 1
    print('read_parameters_from_file_lines: Read %d parameters' % nofParameters)
    return parametersDict


def replace_parameters_in_file_lines(fileLines, parametersDict):
    """Evaluate parameters in readLines of file.

    The parameter name instances in the file are identified by a preceding $.

    Input:
    . fileLines: read lines from comma separate values file
    . parametersDict: dictionary of parameter and expression pairs
    Return:
    . dataLines: data lines with parameter name instances replaced by their
      evaluated values
    """
    dataLines = []
    for fLine in fileLines:
        if '$' in fLine:
            pLine = fLine
            # Replace parameters in fLine with their values
            for name, value in parametersDict.items():
                pLine = pLine.replace('$%s' % name, interfacefiles.value_to_str(value))
            # Evaluate entries with parameters in fLine
            fLineEntries = interfacefiles.get_file_line_entries(fLine)
            pLineEntries = interfacefiles.get_file_line_entries(pLine)
            eLineEntries = []
            for fEntry, pEntry in zip(fLineEntries, pLineEntries):
                if '$' in fEntry:
                    # Evaluate entry
                    value = _eval_expression(pEntry)
                    eLineEntries.append(interfacefiles.value_to_str(value))
                else:
                    # Keep entry
                    eLineEntries.append(pEntry)
            eLine = interfacefiles.put_file_line_entries(eLineEntries)
            dataLines.append(eLine)
        else:
            # Keep fLine
            dataLines.append(fLine)
    return dataLines


def print_parameters_dict(parametersDict):
    """Print parameters.

    Input:
    . parametersDict: dictionary of parameter and expression pairs
    """
    if parametersDict:
        print('Parameters:')
        for name, value in parametersDict.items():
            print('. %-20s = %s' % (name, interfacefiles.value_to_str(value)))
    else:
        print('No parameters.')


def _validate_parameter_name_in_dict(name, parametersDict):
    """Validate whether name is a valid parameter name for parametersDict

    Input:
    . name: parameter name
    . parametersDict: dictionary with already existing parameter and
        expression pairs
    Return: Empty string when validate went OK, else message string about why
        entries are not OK.
    """
    # Ensure parameter name is defined once, so value is constant
    if name in parametersDict.keys():
        return 'Duplicate identical parameter name %s' % name
    # Ensure start of one parameter name is not identical to another parameter
    # name, to avoid partial parameter name substitution
    for k in parametersDict.keys():
        if name in k:
            if name == k[0:len(name)]:
                return 'Duplicate parameter name %s in start of other name' % name
        if k in name:
            if k == name[0:len(k)]:
                return 'Duplicate other name in start of parameter name %s' % name
    # Check that parameter name is valid
    nameMsg = _validate_parameter_name_format(name)
    if nameMsg:
        return nameMsg
    return ''


def _validate_parameter_name_format(name):
    """Validate that the name string is a valid parameter name

    Only accept parameters that:
    . contain only [a-zA-Z0-9_]
    . have maximum one '_' in series

    Input: Parameter name
    Output: Empty string when name is OK, else message string about why name
      is not OK.
    """
    if name == '':
        return 'Parameter name is empty string'
    if '__' in name:
        return 'Illegal double underscore in parameter name %s' % name
    # Find all [a-zA-Z0-9_] in name, yields list of matching valid chars,
    # so without all illegal chars
    charList = re.findall(r'\w', name)
    # Convert list of char into single string
    valName = ''
    for ch in charList:
        valName += '%s' % ch
    if valName in _mathDict:
        return 'Parameter name %s is math function' % name
    if name == valName:
        # Parameter name is valid
        return ''
    else:
        return 'Illegal character in parameter name %s' % name


def _parse_parameter_expression(expression, parametersDict):
    """Replace parameter names from parametersDict in expression.

    Input:
    . expression: parameter expression string
    . parametersDict: Dictionary of parameter and expression pairs
    Return: expression with parameter names replaced by literals
    """
    for name, value in parametersDict.items():
        expression = expression.replace(name, interfacefiles.value_to_str(value))
    return expression


def _eval_expression(expression, safeDict=_mathDict):
    """Safe eval by restricting input to dict of math functions.

    Input:
    . expressionS: expression string to evalute with eval()
    . safeDict: dictionary of safe functions and variables, default only
      allow math functions and literals
    Output:
    . eval() result of expression

    References:
    . https://realpython.com/python-eval-function/#restricting-the-use-of-built-in-names
    """
    # Compile the expression to bytecode. This will raise a SyntaxError if
    # the expression is and invalid expression
    code = compile(expression, '<string>', 'eval')
    # Check .co_names on the bytecode object to make sure it contains only
    # allowed names.
    for name in code.co_names:
        if name not in safeDict:
            # Raise a NameError name is not allowed.
            raise NameError(f'Use of {name} not allowed')
    return eval(code, {'__builtins__': {}}, safeDict)
