(defun myZip (a b)
  (mapcar #'list a b ))

(pprint (myZip '(1 2) '(1 2)))