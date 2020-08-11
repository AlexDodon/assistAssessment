import os
import subprocess
import argparse
import zipfile
import shutil
import xml.etree.ElementTree as ET

def evaluateSourceOnTest(source, test, language):
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

        os.mkdir('/tmp/assistAssessment')
        f = open('/tmp/assistAssessment/toEvalFile.hs','w')
        f.write(toEvalFile)
        f.close()

        p = subprocess.run(['ghci', '/tmp/assistAssessment/toEvalFile.hs'], input='main', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        result = p.stdout

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
        names.append(studentDir)
        
        studentDir = os.path.join(dirPath,studentDir)
        files = os.listdir(studentDir)
        files.sort()

        files = [os.path.join(studentDir,file) for file in files]

        studentSources = [open(file).read() for file in files]

        sources.append(studentSources)

    return (names, sources)

def unzipTo(sourcePath, unzippedDirectory):
    with zipfile.ZipFile(sourcePath,'r') as zip_ref:
        zip_ref.extractall(unzippedDirectory)

    for studentDir in os.listdir(unzippedDirectory):
        studentDir = os.path.join(unzippedDirectory,studentDir)
        
        assert os.path.isdir(studentDir), 'Found unexpected file in archive: ' + studentDir
    
        studentDirContents = os.listdir(studentDir)

        assert len(studentDirContents) == 1, 'Expected a single file in student directory.'

        problemsArchive = os.path.join(studentDir,studentDirContents[0])
        
        with zipfile.ZipFile(problemsArchive,'r') as zip_ref:
            zip_ref.extractall(studentDir)
        
        os.remove(problemsArchive)

def readSourceArchive(sourcePath):
    unzippedDirectory = sourcePath.replace('.zip','')
    
    if not os.path.isdir(unzippedDirectory):  
        os.mkdir(unzippedDirectory)
    
        unzipTo(sourcePath,unzippedDirectory)

    return readSourceDir(unzippedDirectory)

def getAnswersAndTests(problemPathList, languageList):
    solutions = []
    tests = []
    for problem, language  in zip(problemPathList, languageList):
        root = ET.parse(problem).getroot()
    
        for solution in root.findall('solution'):
            if solution.attrib['language'] == language:
                solutions.append(solution.text)
                break
        
        for test in root.findall('tests'):
            if test.attrib['language'] == language:
                tests.append(test.text)
                break

    answers = [evaluateSourceOnTest(solution, test, language) for solution, test, language in zip(solutions, tests, languageList)]

    return (answers,tests)

def evaluateArchive(sourcePath, answers, tests, languageList):
    names, sources = readSourceArchive(sourcePath)
    numberOfProblems = len(answers)
    grades = []
    count = []
    maxNameLength = 0

    for student, studentSources in zip(names, sources):
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('------------------------------------------------')
        print('\n\tGrading ' + student + '\'s solutions:\n')

        if maxNameLength < len(student):
            maxNameLength = len(student)
        
        studentScore = 0
        numberOfStudentSources = len(studentSources)

        if numberOfStudentSources == numberOfProblems:
            for answer, language, studentSource, test in zip(answers, languageList, studentSources, tests):
                studentAnswer = evaluateSourceOnTest(studentSource, test, language)

                if gradeStudentAnswer(studentAnswer, answer, student):
                    studentScore += 1
            
            grade = '{}/{}'.format(studentScore,numberOfProblems)

            print('------------------------------------------------')
            print(student + ' has solved correctly ' + grade + ' problems.')

            grades.append(grade)
        else:
            print(student + ' has less source files than expected. Not grading any.')
            grades.append('N/A')
            
        count.append('{}/{}'.format(numberOfStudentSources,numberOfProblems))
    
    print('------------------------------------------------')
    print('------------------------------------------------')
    print('------------------------------------------------')
    print('Results:\n')
    
    print('{:30}| {:20}| {}'.format('Name', 'Number of sources', 'Grade'))
    print('------------------------------------------------------------')
    for line in zip(names, count, grades):
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


def evaluate(args):
    problemPathList = args.problemPathList
    sourcePathList = args.sourcePathList
    archive = args.archive
    languageList = args.languageList

    answers, tests = getAnswersAndTests(problemPathList, languageList)    

    if archive:
        evaluateArchive(sourcePathList[0], answers, tests, languageList)
    else:
        evaluateStandaloneSources(sourcePathList, answers, tests, languageList)
    
def validateArgs(args):
    assert len(args.problemPathList) == len(args.languageList), 'The number of -l arguments must match the number of -p arguments.'

    if args.archive:
        assert len(args.sourcePathList) == 1, 'When using -a, pass a single -s argument'
    else:
        assert len(args.sourcePathList) == len(args.languageList), 'When evaluating independent source files(no -a), the number of -s arguments must match the number of -l and -p arguments'

def getArgs():
    parser = argparse.ArgumentParser(description='Script that assists in creating programming problems and evaluating solutions to them.')

    parser.add_argument('-E','--evaluate', dest='command', action='store_const',
        const=evaluate, help='Mutually exclusive with -F. Evaluate the source[s] specified by -s with regard to the problem specified by -p.')

    parser.add_argument('-p','--problem-path', dest='problemPathList', action='append', metavar='problemPath', 
        help='Path to a problem file. Can pass multiple times to specify multiple problem files. Useful with -d. For each student\'s source files, the problem files are considered in the specified order.')

    parser.add_argument('-s','--source-path', dest='sourcePathList', action='append', metavar='sourcePath',
        help='Path to source file[s] to be evaluated. Usually point to an archive with multiple students with -d. Can evaluate a source file independently by not passing -d. Can pass multiple times to evaluate multiple sources independently or multiple archives.')

    parser.add_argument('-a','--is-archive', dest='archive', action='store_const', const=True, default=False,
        help='specifies the source path to be a path to an archive of sources.')
        
    parser.add_argument('-l','--language', dest='languageList', action='append', metavar='language',
        help='Specifies the programming language that will be used to evaluate. Accepts \"Python\", \"Haskell\", \"ML\", \"Lisp\". Can specify multiple languages. Order matters. If multiple languages specified, will consider matching sources to be')

    return parser.parse_args()

def main():
    args = getArgs()

    validateArgs(args)

    args.command(args)

if __name__ == '__main__':
    main()