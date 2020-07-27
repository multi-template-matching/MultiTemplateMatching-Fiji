from org.bytedeco.javacpp.opencv_dnn import NMSBoxes # https://www.javadoc.io/static/org.bytedeco.javacpp-presets/opencv/3.4.2-1.4.2/org/bytedeco/javacpp/opencv_dnn.html
import org.bytedeco.javacpp.opencv_core as cv2
from org.bytedeco.javacpp import FloatPointer, IntPointer


listBoxes = [(946, 784, 414, 400), (1525, 968, 414, 400), (1533, 960, 414, 400), (947, 784, 400, 414), (1173, 1354, 414, 400), (1459, 474, 400, 414), (1021, 888, 414, 400), (1450, 492, 400, 414), (1398, 889, 414, 400), (1005, 872, 400, 414), (686, 1367, 414, 400), (697, 1371, 414, 400), (694, 1371, 414, 400), (1128, 1377, 414, 400), (950, 787, 414, 400), (1438, 481, 414, 400), (1064, 1238, 414, 400), (1455, 485, 414, 400), (111, 787, 414, 400), (109, 782, 414, 400)]
listScore = [1.0, 0.5919371843338013, 0.5894666314125061, 0.5689446926116943, 0.5510676503181458, 0.5381054282188416, 0.5311822891235352, 0.5298448204994202, 0.5123124122619629, 0.511840283870697, 0.5080571174621582, 0.5080069303512573, 0.5079731941223145, 0.5000045895576477, 0.49151238799095154, 0.4728872776031494, 0.4612887501716614, 0.4540329873561859, 0.4483684003353119, 0.44806933403015137]
listRect = [None] * len(listBoxes)

for i, box in enumerate(listBoxes):
	listRect[i] = cv2.Rect(*box)

bboxes = cv2.RectVector(listRect)
scores = FloatPointer(listScore)

indices1 = IntPointer()
NMSBoxes(bboxes, scores, 0.4, 0.3, indices1, 1.0, 4)
print indices1

indices2 = IntPointer()
NMSBoxes(bboxes, scores, 0.4, 0.3, indices2)
print indices2
