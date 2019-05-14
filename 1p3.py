import pandas as pd
import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--name', type=str, default='nobody')
	parser.add_argument('--result', type=str, default='result.csv')
	parser.add_argument('--column', type=str, default='rcmd')
	args = parser.parse_args()

	groundtruth = pd.read_csv('test.csv')
	prediction = pd.read_csv(args.result)

	# =>T/F
	groundtruth['rating'] = groundtruth['rating'] > 6    # >6 then recommend
	prediction[args.column] = prediction[args.column] == 1

	groundtruth = groundtruth.rename(columns={'rating':'gt'})
	result = pd.merge(groundtruth, prediction)

	gt_tlist = result[result['gt']==True].index
	gt_flist = result[result['gt']==False].index
	pred_tlist = result[result[args.column]==True].index
	pred_flist = result[result[args.column]==False].index

	TP = gt_tlist.intersection(pred_tlist)
	TN = gt_flist.intersection(pred_flist)
	FP = gt_flist.intersection(pred_tlist)
	FN = gt_tlist.intersection(pred_flist)

	precision = len(TP) / (len(TP) + len(FP))
	recall = len(TP) / (len(TP) + len(FN))
	accuracy = (len(TP) + len(TN)) / len(result)
	f1 = 2 * precision * recall / (precision + recall)

	sheet = pd.read_csv('sheet.csv')
	row = {'name':args.name,'precision':precision,'recall':recall,'accuracy':accuracy,'F1':f1}
	sheet = sheet.append(row,ignore_index=True)
	sheet.to_csv('sheet.csv', index=False)

	print('saved.')
	print('precision:', precision)
	print('recall:', recall)
	print('accuracy:', accuracy)
	print('F1:', f1)
