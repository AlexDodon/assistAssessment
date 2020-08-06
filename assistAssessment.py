import os
import subprocess
import argparse
import zipfile
import xml.etree.ElementTree as ET

def evaluateOne(solution, test, language):
    result = ''

    if language == 'Python':
        solution += '\n'
        for testLine in test.split('\n'):
            if testLine != '':
                solution += 'print(' + testLine + ')\n'
        
        p = subprocess.run('python', input=solution, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        result = p.stdout

    return result

def grade(result, answer, source):
    print('------------------------------------------------')
    print('The source file\n\n\t' + source + '\n\nhas produced the answer:\n')
    print(result)
    print('------------------------------------------------')
    print('The correct answer was:\n')
    print(answer)
    print('------------------------------------------------')
    if result == answer:
        print('The solution given by the student is correct.')
    else:
        print('The solution given by the student is wrong.')
    print('------------------------------------------------')

def evaluate(problemPathsList, sourcePathsList, archive):
    solutions = []
    tests = []
    language = ''
    for problem in problemPathsList:
        root = ET.parse(problem).getroot()
        solutions.append(root.find('solution').text)
        tests.append(root.find('tests').text)
        language = root.attrib['language']

    answers = [evaluateOne(solution,test,language) for solution,test in zip(solutions,tests)]
    
    if archive:
        for source in sourcePathsList:
            unzippedDirectory = source.replace('.zip','')
            
            if not os.path.isdir(unzippedDirectory):  
                os.mkdir(unzippedDirectory)
            
            with zipfile.ZipFile(source,'r') as zip_ref:
                zip_ref.extractall(unzippedDirectory)

            for studentDir in os.listdir(unzippedDirectory):
                studentDir = os.path.join(unzippedDirectory,studentDir)
                
                if os.path.isdir(studentDir):
                    for problemsArchive in os.listdir(studentDir):
                        problemsArchive = os.path.join(studentDir,problemsArchive)
                        
                        with zipfile.ZipFile(problemsArchive,'r') as zip_ref:
                            zip_ref.extractall(studentDir)
                       
                        os.remove(problemsArchive)

                    files = os.listdir(studentDir)
                    files.sort()

                    for studentSource, answer, test in zip(files, answers, tests):
                        studentSource = os.path.join(studentDir, studentSource)

                        print(studentDir)
                        print(studentSource)
                        print(answer)
                        print(test)

                        with open(studentSource) as studentSourceFile:
                            grade(evaluateOne(studentSourceFile.read(), test, language), answer, studentSource)

                else:
                    print('Found unexpected file in archive: ' + studentDir)

    else:
        for source,test, answer in zip(sourcePathsList, tests, answers):
            with open(source) as sourceFile:
                grade(evaluateOne(sourceFile.read(),test,language), answer, source)

    


def main():
    parser = argparse.ArgumentParser(description='Script that assists in creating programming problems and evaluating solutions to them.')

    parser.add_argument('-E','--evaluate', dest='command', action='store_const',
        const=evaluate, help='Mutually exclusive with -F. Evaluate the source[s] specified by -s with regard to the problem specified by -p.')
    parser.add_argument('-p','--problem-path', dest='problemPath', action='append', 
        help='Path to a problem file. Can pass multiple times to specify multiple problem files. Useful with -d. For each student\'s source files, the problem files are considered in the specified order.')
    parser.add_argument('-s','--source-path', dest='sourcePath', action='append',
        help='Path to source file[s] to be evaluated. Usually point to an archive with multiple students with -d. Can evaluate a source file independently by not passing -d. Can pass multiple times to evaluate multiple sources independently or multiple archives.')
    parser.add_argument('-a','--is-archive', dest='archive', action='store_const',
        const=True, default=False, help='specifies the source path to be a path to an archive of sources.')

    args = parser.parse_args()

    if args.command == evaluate:
        evaluate(args.problemPath, args.sourcePath, args.archive)

if __name__ == '__main__':
    main()