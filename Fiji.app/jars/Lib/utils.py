def AddToTable(Table, Dico, Order=None, Label=""):
	'''
	Append a row to an existing result table
	Dico  : {'column1':value1, 'column2':value2...} - NB: The column header of the dictionnary should match the one of the existing table
	Order : ('column1', 'column2',...), if one wants to specify an order for the column
	Label : (optional) String to use as row index, if empty then only columns in the table
	'''
	# add new row 
	Table.incrementCounter() 
	
	# Define the Label for that row = row index
	if Label: Table.addLabel(Label) # otherwise there are only columns 
	
	if Order and set(Order)==set(Dico.keys()): # check that the content of order is indeed equal to the content of dico keys
		for key in Order: # we loop over order to have the keys ordonned
			Table.addValue(key, Dico[key])
	
	else: # When the content of order is not equal to the content of the dico. Then just iterate over the dictionnary without a specific order
		for key, value in Dico.iteritems():
			Table.addValue(key, value)
		

		
if __name__ in ['__main__', '__builtin__']:
	from ij.measure import ResultsTable

	Table = ResultsTable()

	AddToTable(Table, {'Column1':5, 'Column2':41}, Order=("Column2", "Column1"), Label='Line1')
	AddToTable(Table, {'Column1':5, 'Column2':41}, Order=("Column2", "Column1"), Label='Line2')

	Table.show("Results")