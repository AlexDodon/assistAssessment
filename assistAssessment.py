import os
import subprocess
import argparse
import shutil
import itertools
import xml.etree.ElementTree as ET

def evaluateSourceOnTest(source, test, language):
    #Central point for executing code
    #From each execution it just captures stdout and stderr
    #Because of this, generally, each test (line) is wrapped by some print statement
    #If there are problems with dependencies, change the command run in supbrocess.run; for example, in the case of Haskell use the system ghc instead of the stack ghc by changing the command list to ['ghc', '-o', '/tmp/sol', '/tmp/assistAssessment/toEvalFile.hs']
    result = ''
    if language == 'Python':
        source += '\n'
        for testLine in test.split('\n'):
            if testLine != '':
                source += 'print(' + testLine + ')\n'
        
        p = subprocess.run('python', input=source, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        result = p.stdout

    if language == 'Haskell':
        toEvalFile = 'main::IO()\nmain = do\n'
        for testLine in test.split('\n'):
            if testLine != '':
                toEvalFile += 'putStrLn . show $ ' + testLine + '\n'
        
        toEvalFile += 'where\n' + source

        try: #The try blocks are to assure we clean up 
            os.mkdir('/tmp/assistAssessment')
            f = open('/tmp/assistAssessment/toEvalFile.hs','w')
            f.write(toEvalFile)
            f.close()

            p = subprocess.run(['stack', 'ghc','--', '-o', '/tmp/sol', '/tmp/assistAssessment/toEvalFile.hs'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            p = subprocess.run('/tmp/sol', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            result = p.stdout

        finally:
            shutil.rmtree('/tmp/assistAssessment')

    if language == 'CommonLisp':
        source += '\n'
        for testLine in test.split('\n'):
            if testLine != '':
                source += '(pprint ' + testLine + ')\n'

        try:
            os.mkdir('/tmp/assistAssessment')
            f = open('/tmp/assistAssessment/toEvalFile.lsp','w')
            f.write(source)
            f.close()
            
            p = subprocess.run(['sbcl', '--script', '/tmp/assistAssessment/toEvalFile.lsp'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            result = p.stdout[1:]

        finally:
            shutil.rmtree('/tmp/assistAssessment')

    if language == 'PolyML':
        programInput = ''
        for testLine in test.split('\n'):
            if testLine != '':
                programInput += testLine

        try:
            os.mkdir('/tmp/assistAssessment')
            f = open('/tmp/assistAssessment/toEvalFile.ml','w')
            f.write(source)
            f.close()
            
            p = subprocess.run(['poly', '--use', '/tmp/assistAssessment/toEvalFile.ml'], input=programInput, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            result = '\n'.join(p.stdout.split('val it = ')[1:])

        finally:
            shutil.rmtree('/tmp/assistAssessment')

    return result

def gradeStudentAnswer(studentAnswer, answer, student):
    print('------------------------------------------------')
    print('For the correct answer:\n')
    print(answer)
    print('------------------------------------------------')
    print('The student\n\n\t' + student + '\n\nhas produced the answer:\n')
    print(studentAnswer)
    print('------------------------------------------------')
    if studentAnswer == answer:
        print('The given solution is correct.')
        print('------------------------------------------------')
        return True
    else:
        print('The given solution is wrong.')
        print('------------------------------------------------')
        return False

def readSourceDir(dirPath):
    names = []
    sources = []

    for studentDir in os.listdir(dirPath):
        names.append(studentDir) #Assumes the directories are named after the names of students
        
        studentDir = os.path.join(dirPath,studentDir)
        files = os.listdir(studentDir)
        files.sort()#Probably not necessary

        files = [os.path.join(studentDir,file) for file in files]

        studentSources = [open(file).read() for file in files]

        sources.append(studentSources)

    return (names, sources)

def unpackTo(sourcePath, unpackedDirectory):
    #This function should unpack the archive in a format of containing_dir->many student_dirs->each having source files(one per problem)
    #As of now, it assumes the archive to contain a number of student dirs, each containing an archive with source files; If another archive structure is desired, this code should be rewrote, but the unpacked directory's structure should probably remain the same; otherwise rewrite readSourceDir
    shutil.unpack_archive(sourcePath, unpackedDirectory)

    for studentDir in os.listdir(unpackedDirectory):
        studentDir = os.path.join(unpackedDirectory,studentDir)
        
        assert os.path.isdir(studentDir), 'Found unexpected file in archive: ' + studentDir
    
        studentDirContents = os.listdir(studentDir)

        assert len(studentDirContents) == 1, 'Expected a single file in student directory.'

        problemsArchive = os.path.join(studentDir,studentDirContents[0])
        
        shutil.unpack_archive(problemsArchive, studentDir)
        
        os.remove(problemsArchive)

def readSourceArchive(sourcePath):
    unpackedDirectory = sourcePath.replace('.zip','')
    
    if not os.path.isdir(unpackedDirectory):  
        os.mkdir(unpackedDirectory)
    
        unpackTo(sourcePath,unpackedDirectory)

    return readSourceDir(unpackedDirectory)

def parseProblemFiles(problemPathList, languageList):
    #Central point for interfacing with the xml specification file
    texts = []
    examples = []
    solutions = []
    tests = []
    for problem, language  in zip(problemPathList, languageList):
        root = ET.parse(problem).getroot()
    
        for text in root.findall('text'):
            texts.append(text.text)
            break

        for example in root.findall('example'):
            if example.attrib['language'] == language:
                examples.append(example.text)
                break

        for solution in root.findall('solution'):
            if solution.attrib['language'] == language:
                solutions.append(solution.text)
                break
        
        for test in root.findall('tests'):
            if test.attrib['language'] == language:
                tests.append(test.text)
                break

    return (texts, examples, solutions, tests)

def evaluateArchive(sourcePath, answers, tests, languageList):
    studentsNames, sources = readSourceArchive(sourcePath)
    numberOfProblems = len(answers)
    grades = []
    count = []
    answersPermutations = list(itertools.permutations(answers))

    for studentName, studentSources in zip(studentsNames, sources):
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('\n\tGrading ' + studentName + '\'s solutions:\n')

        studentMaxScore = 0

        for answersPerm in answersPermutations: 
            print('------------------------------------------------')
            print('Testing a new permutation of answers.')
        
            studentScore = 0

            for answer, language, studentSource, test in zip(answersPerm, languageList, studentSources, tests):
                studentAnswer = evaluateSourceOnTest(studentSource, test, language)

                if gradeStudentAnswer(studentAnswer, answer, studentName):
                    studentScore += 1
            
            tempGrade = '{}/{}'.format(studentScore,numberOfProblems)

            print('For this permutation of answers, ' + studentName + ' has solved correctly ' + tempGrade + ' problems.')
            print('------------------------------------------------')
            
            if studentScore > studentMaxScore:
                studentMaxScore = studentScore

            if studentMaxScore == numberOfProblems:
                break

        grade = '{}/{}'.format(studentMaxScore,numberOfProblems)

        print('------------------------------------------------')
        print('In the end, ' + studentName + ' has solved correctly ' + grade + ' problems.')

        grades.append(grade)
            
        count.append('{}/{}'.format(len(studentSources),numberOfProblems))
    
    print('------------------------------------------------')
    print('------------------------------------------------')
    print('------------------------------------------------')
    print('Results:\n') #Formatting of results is hardcoded; gets thrown off by names that are too long
    
    print('{:30}| {:20}| {}'.format('Name', 'Number of sources', 'Grade'))
    print('------------------------------------------------------------')

    for line in zip(studentsNames, count, grades):
        print('{:30}| {:20}| {}'.format(*line))

def evaluateStandaloneSources(sourcePathList, answers, tests, languageList):
    for sourcePath, answer, test, language in zip(sourcePathList, answers, tests, languageList):
        f = open(sourcePath,'r')
        sourceAnswer = evaluateSourceOnTest(f.read(), test, language)
        f.close()
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('\n\tEvaluating ' + sourcePath + ':\n')
        print('------------------------------------------------')
        print('For the correct answer:\n')
        print(answer)
        print('------------------------------------------------')
        print('The source file \n\n\t' + sourcePath + '\n\nhas produced the answer:\n')
        print(sourceAnswer)
        print('------------------------------------------------')
        if sourceAnswer == answer:
            print('The given solution is correct.')
        else:
            print('The given solution is wrong.')
        print('------------------------------------------------')

def formatTex(text, solution, example, language):
    if language == 'Python':
        text = text[1:-1] #This gets rid of newlines from not having all the text betwen xml tags on a single line
        signature = solution.split('\n')[1][4:-1] #Look at the solution for why it is done like this; assuming the main function is writen from the first line, the split and [1] picks the first line and [4:-1] gets rid of "fun " and ":"
        example = example[1:-1] #Same thing as for the text
    
    if language == 'Haskell':
        text = text[1:-1]
        signature = solution.split("\n")[1]
        example = example[1:-1]
    
    if language == 'CommonLisp':
        text = text[1:-1]
        signature = solution.split("\n")[1][7:]
        example = example[1:-1]
    
    if language == 'PolyML':
        text = text[1:-1]

        try:
            os.mkdir('/tmp/assistAssessment')
            f = open('/tmp/assistAssessment/getSignature.ml','w')
            f.write(solution)
            f.close()
            
            functionName = solution.split(' ')[1]

            p = subprocess.run(['poly', '--use', '/tmp/assistAssessment/getSignature.ml'], input=functionName, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) #After getting the name of the function from the solution, we write it to stdin for the interpreter and get its signature
            
            signature = functionName + p.stdout.split('\n')[-2][6:]

        finally:
            shutil.rmtree('/tmp/assistAssessment')

        example = example[1:-1]

    examples = example.split('\n')
    results = [evaluateSourceOnTest(solution, ex, language)[:-1] for ex in examples]
    examplesAndResults = list(zip(examples, results))

    texWrapper = lambda s : '\\texttt{' + s + '}'

    genericExample = 'E.g. '
    for i, (ex, result) in enumerate(examplesAndResults):
        genericExample += texWrapper(ex) + ' should return ' + texWrapper(result)
        
        if i < len(examplesAndResults) - 2:
            genericExample += ', '
        if i == len(examplesAndResults) - 2:
            genericExample += ', while '
        if i == len(examplesAndResults) - 1:
            genericExample += '.'

    #Here, you can change all the tags for formatting without changing functionality.
    finalText = text.replace( #Here we replace ALL occurences of [[function]] and [[genericExample]]
        '[[function]]',
        texWrapper(signature)
    ).replace(
        '[[genericExample]]',
        genericExample
    )

    for ex, result in examplesAndResults:
        finalText = finalText.replace( #Here we replace ONLY THE FIRST occurence; hence we can have more and loop through examples
            '[[callExample]]',
            texWrapper(ex),
            1
        ).replace(
            '[[exampleResult]]',
            texWrapper(result),
            1
        )

    return finalText

def format(args):
    problemPathList = args.problemPathList
    languageList = args.languageList
    texts, examples, solutions, _ = parseProblemFiles(problemPathList,languageList)

    for problemPath, text, example, solution , language in zip(problemPathList, texts, examples, solutions, languageList):
        finalTex = ''
        ouptutPath = problemPath.replace('.xml','.' + language + '.tex')

        finalTex = formatTex(text,solution,example,language)
        
        print(finalTex +'\n\n')

        with open(ouptutPath,"w") as finalFile:
            finalFile.write(finalTex)
            finalFile.close()

def evaluate(args):
    problemPathList = args.problemPathList
    sourcePathList = args.sourcePathList
    archive = args.archive
    languageList = args.languageList

    _, _, solutions, tests = parseProblemFiles(problemPathList, languageList)    

    answers = [evaluateSourceOnTest(solution, test, language) for solution, test, language in zip(solutions, tests, languageList)]

    if archive:
        evaluateArchive(sourcePathList[0], answers, tests, languageList) # The source path is still given as a list even if there is only one
    else:
        evaluateStandaloneSources(sourcePathList, answers, tests, languageList)
    
def validateArgs(args):
    assert args.command == format or args.command == evaluate, 'Must pass either -F or -E.'

    assert len(args.problemPathList) == len(args.languageList), 'The number of -l arguments must match the number of -p arguments.' #This matters for both format and evaluate
    
    if args.command == evaluate:
        if args.archive:
            assert len(args.sourcePathList) == 1, 'When using -a, pass a single -s argument'
        else:
            assert len(args.sourcePathList) == len(args.languageList), 'When evaluating independent source files(no -a), the number of -s arguments must match the number of -l and -p arguments'

def getArgs():
    parser = argparse.ArgumentParser(description='Script that assists in creating programming problems and evaluating solutions to them.')

    bar=parser.add_mutually_exclusive_group()
    bar.add_argument('-E','--evaluate', dest='command', action='store_const',
        const=evaluate, help='Mutually exclusive with -F. Evaluate the source[s] specified by -s with regard to the problem specified by -p and it\'s desired language specified by -l')
    
    
    bar.add_argument('-F','--format', dest='command', action='store_const',
        const=format, help='Mutually exclusive with -E. Format the problem text specified by -p and the desired language specified by -l to a latex format.')

    
    parser.add_argument('-p','--problem-path', dest='problemPathList', action='append', metavar='problemPath', 
        help='Path to a problem file. Can pass multiple times to specify multiple problem files. For each -p, you should specify a -l. With regards to -E, if using -a, that means that each student should have solved that many problems. Students that have less source files in their archive will not be graded')

    parser.add_argument('-s','--source-path', dest='sourcePathList', action='append', metavar='sourcePath',
        help='Path to source file[s] to be evaluated. With regards to -E, when using -a, it should point to an archive and be passed a single time. Otherwise, each source file specified by -s corresponds to a problem description given by -p.')

    parser.add_argument('-a','--is-archive', dest='archive', action='store_const', const=True, default=False,
        help='When using -E, -a specifies the source path to be a path to an archive of sources. When used, should pass a single -s.')
        
    parser.add_argument('-l','--language', dest='languageList', action='append', metavar='language',
        help='Specifies the programming language that, in case of -E, will be used to evaluate the sources and in case of -F to populate the text. Accepts \"Python\", \"Haskell\", \"PolyML\", \"CommonLisp\". Each problem description given by -p should have a coresponding -l that specifies the language that should be used. XML tags with the appropriate language attribute should be found in the problem description.')

    return parser.parse_args()

def main():
    args = getArgs()

    validateArgs(args)

    args.command(args) #Based on the -E or -F flag, executes functionality

if __name__ == '__main__':
    main()