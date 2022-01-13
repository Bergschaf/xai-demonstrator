import random
from urllib.request import urlopen
from urllib.error import URLError
import requests
from .explainer.explain import explain_cnn, convert_explanation
from fastapi import APIRouter, UploadFile, File
from .model.predict import load_model, load_image, predict_image, preprocess
from shapely.geometry import Point, Polygon
from .config import settings
import base64
import uuid

api = APIRouter()

#To-DO: Polygons und Model auserhalb von Funktionen programmieren, damit diese im RAM sind

def generate_random(polygon):
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < 1:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            points.append(pnt)
    return list(points[0].coords)


# Google Street View Image API
# 25,000 image requests per 24 hours
# See https://developers.google.com/maps/documentation/streetview/
API_KEY = settings.google_maps_api_token
GOOGLE_URL = (
    "http://maps.googleapis.com/maps/api/streetview?size=448x448&sensor=false&"
    "size=640x640&source=outdoor&key=" + API_KEY
)

API_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"  # Not billed

IMG_PREFIX = "img_"
IMG_SUFFIX = ".png"

hamburg = {
        "country": "Germany",
        "city": "Hamburg",
        "polygon": [(9.9531893, 53.5463685), (9.9475245, 53.5460625), (9.9410014, 53.5461645), (9.9351649, 53.5463175), (9.9317317, 53.5465725), (9.9292426, 53.5462155), (9.9232344, 53.5461645), 
                    (9.9177413, 53.5457565), (9.9127631, 53.5461645), (9.9089007, 53.5459605), (9.9149089, 53.5432575), (9.9182563, 53.5419824), (9.9276118, 53.538004), (9.9319892, 53.5357596), (9.933105, 53.533464), (9.9339633, 53.5300459), (9.9328475, 53.527597), (9.9295001, 53.5243826), (9.9250369, 53.5212189), (9.9212603, 53.5188716), (9.9229769, 53.5177999), (9.9252944, 53.5177488), (9.9275198, 53.5188044), (9.9283843, 53.5201473), (9.9303584, 53.5217802), (9.9322467, 53.5223415), (9.9357657, 53.5222395), (9.9424605, 53.521321), (9.9474387, 53.5202494), (9.952846, 53.5189226), (9.9576525, 53.517953), (9.9637465, 53.5167282), (9.9663214, 53.5158606), (9.9692397, 53.5150951), 
                    (9.9688964, 53.5128494), (9.9726729, 53.512288), (9.9749903, 53.5119818), (9.9769644, 53.5112672), (9.976707, 53.5106547), (9.9758486, 53.5092766), (9.9764495, 53.5072859), 
                    (9.9785094, 53.5067754), (9.9815993, 53.5062139), (9.9828009, 53.5051419), (9.9831443, 53.5034573), (9.98529, 53.5017216),
                    (9.9876933, 53.5007516), (9.9917273, 53.5005984), (9.9934439, 53.500241), (9.9991088, 53.4987604), (10.0001387, 53.499322), (10.0018553, 53.5007516), (10.003572, 53.5019768), (10.0040011, 53.5036104), (10.0040011, 53.5059587), (10.0062327, 53.5060097), (10.0058036, 53.5093276), (10.0052027, 53.5120328), (10.0052027, 53.5138702), (10.0063185, 53.5152992), (10.0082926, 53.5161668), (10.0113826, 53.5167792), (10.0130992, 53.5168813), (10.0151591, 53.5163199), (10.0165324, 53.516524), (10.0162749, 53.5175447), (10.0200515, 53.5174937), (10.0246005, 53.5168813), (10.0285487, 53.5163199), (10.0307803, 53.5151971), (10.0322394, 53.5135129), 
                    (10.034471, 53.511012), (10.0362735, 53.5101953), (10.038505, 53.509787), (10.0424533, 53.509838), (10.0506072, 53.5095828), (10.0597911, 53.5092766), (10.0671725, 53.5090724), (10.0717215, 53.5083578), (10.0778155, 53.507439), (10.0859694, 53.5072859), (10.0903897, 53.5037636), (10.0909047, 53.5050143), (10.0907759, 53.5077708), (10.0906901, 53.5099146), (10.0889958, 53.5113982), (10.0863986, 53.5130025), (10.0771289, 53.518795), (10.0711636, 53.5224946), (10.0691466, 53.5239999), (10.0687398, 53.5249472),
                    (10.0694899, 53.5261939), (10.0712495, 53.5272909), (10.0738244, 53.5283878), (10.0772147, 53.5297908), (10.0806479, 53.5315764), (10.0815491, 53.5332344), (10.0827079, 53.5355555), (10.0838237, 53.5377744), (10.083652, 53.5411919), (10.0833087, 53.5440225), (10.083137, 53.5455525), (10.0838237, 53.546547), (10.0848107, 53.547414), (10.0857548, 53.5484594), (10.0857548, 53.5493773), (10.0848107, 53.5505247), (10.0843816, 53.5515445), (10.0843386, 53.5529978), (10.084639, 53.5537371), (10.0843816, 53.5546549), (10.0832658, 53.5552158), (10.0826649, 53.556261), (10.08112, 53.5592946), (10.0794892, 53.5624554), (10.0782876, 53.5642906), 
                    (10.0766139, 53.5664315), (10.0757985, 53.5671197), (10.0735669, 53.5681901), (10.0727515, 53.569235), (10.0723223, 53.5703309), (10.0717215, 53.5712738), (10.0706916, 53.5725225), (10.0703482, 53.573236), (10.0697903, 53.574765), (10.0703053, 53.5764722), (10.0698333, 53.5782813), (10.0696187, 53.5797337), (10.0686745, 53.5805745), (10.0678162, 53.5821031), (10.0671296, 53.5834025), (10.0659709, 53.5851094), (10.063868, 53.5871474), (10.0621085, 53.5884466), (10.0594477, 53.5898476), (10.0563149, 53.5912486), (10.0524955, 53.5929043),
                    (10.0482897, 53.5950438), (10.0419383, 53.5985839), (10.0408654, 53.5989914), (10.0377755, 53.6003411), (10.0354581, 53.6011051), (10.0325398, 53.6009523), (10.028892, 53.6001629), (10.0255017, 53.6003411), (10.0182061, 53.6005703), (10.0158457, 53.6001629), (10.0109963, 53.599679), (10.0067048, 53.5993734), (10.0057177, 53.5997045), (10.0031428, 53.6006467), (10.0008254, 53.6013853), (9.997993, 53.6018946), (9.9946027, 53.601971), (9.9921994, 53.6022002), (9.9882512, 53.604823), 
                    (9.9864917, 53.6031424), (9.9851184, 53.602302), (9.9847321, 53.6013853), (9.9839596, 53.6007486), (9.9838738, 53.5992715), (9.9839596, 53.5974888), (9.9838309, 53.5956041), (9.9839596, 53.5938976), (9.9839596, 53.5924203), (9.9835734, 53.5911977), (9.9829726, 53.5903061), (9.9824147, 53.5898986), (9.9809127, 53.5890834), (9.9773507, 53.5876314), (9.9749045, 53.5868927), (9.9731879, 53.5861284), (9.9715571, 53.5850839), 
                    (9.970613, 53.5843451), (9.9689822, 53.5840903), (9.9681668, 53.5838611), (9.9674372, 53.5831732), (9.9665789, 53.5823834), (9.966021, 53.5816445), (9.9649911, 53.5810586), (9.9639182, 53.5797082), (9.9629311, 53.5787145), (9.9615578, 53.5771602), (9.9608712, 53.5762684),
                    (9.9596696, 53.5752236), (9.9592833, 53.5743318), (9.9585967, 53.5732105), (9.9575238, 53.5719873), (9.9561505, 53.5703818), (9.9539618, 53.5693115), (9.9528889, 53.5681646), (9.9515586, 53.5663551), (9.9499707, 53.5640357), (9.9476533, 53.560875), (9.9488549, 53.559524), (9.9495845, 53.5581475), (9.9502711, 53.55621), (9.9508719, 53.5553942), (9.9525456, 53.554349), (9.9549489, 53.5530232), (9.9556355, 53.5519014), (9.9556355, 53.5499637), (9.9548201, 53.5485869), (9.9531893, 53.5463685)]
    }

berlin = {
        "country": "Germany",
        "city": "Berlin",
        "polygon": [(13.4693571, 52.5031835), (13.4699579, 52.5040456), (13.4705158, 52.5048162), (13.4712668, 52.5055738), (13.4720393, 52.5064488), (13.4732194, 52.5076635), (13.474228, 52.5087475), (13.4750433, 52.5096225), (13.4754725, 52.5103016), (13.4757085, 52.5110851), (13.4756442, 52.5116075), (13.4752365, 52.5132529), (13.4748717, 52.514167), (13.4744854, 52.515055), (13.4739705, 52.5158776), (13.4735842, 52.5164783), (13.4710093, 52.5202126), (13.4707089, 52.5208132), (13.470387, 52.5213094), (13.4697218, 52.5220666), (13.4690137, 52.5225105), (13.4677263, 52.5230589), (13.4660311, 52.5234636), (13.4647007, 52.5237247), 
                    (13.4635849, 52.5240511), (13.4623189, 52.5244558), (13.4606667, 52.5250303), (13.4593363, 52.5255655), (13.4589715, 52.526166), (13.458757, 52.5268971), (13.4584136, 52.5276021), (13.4579201, 52.5284245), (13.4575339, 52.529038), (13.4569116, 52.5296646), (13.4560318, 52.5305392), (13.4554525, 52.5311527), (13.4510966, 52.5355254), (13.4495087, 52.5372482), (13.436205, 52.5422597), (13.4333511, 52.5432906), (13.4312482, 52.5441389), (13.4291668, 52.5450654), (13.4268923, 52.5460701), (13.4224506, 52.5479883),
                    (13.4205623, 52.5487712), (13.4183522, 52.5495802), (13.4162708, 52.5501412), (13.4140177, 52.5506631), (13.4094258, 52.5509763), (13.4069796, 52.5511589), (13.4040399, 52.5513546), (13.401701, 52.5512111), (13.3982678, 52.5509371), (13.3932896, 52.5504544), (13.3873673, 52.5499716), (13.3867236, 52.5494758), (13.3859296, 52.5491235), (13.3845349, 52.5488625), (13.3833976, 52.5485102), (13.3831187, 52.5483276), (13.3810158, 52.5481449), (13.3790417, 52.5477012), 
                    (13.3770032, 52.5470488), (13.3748575, 52.5461484), (13.3727761, 52.545222), (13.3686777, 52.5434081), (13.3664246, 52.5424555), (13.3635922, 52.5411896), (13.3611889, 52.5401586), (13.3583351, 52.5388796), (13.3565755, 52.5380182), (13.3548804, 52.5374309), (13.3520051, 52.5370655), (13.3491297, 52.5367261), (13.3460613, 52.5363476), (13.3436795, 52.5361388), (13.3286376, 52.5342071), (13.3282729, 52.5341549), (13.3283158, 52.5329801), (13.31454, 52.5303564), (13.312995, 52.5299779), (13.3111496, 52.529508), (13.3074375, 52.5289597), 
                    (13.3057209, 52.5287508), (13.3043046, 52.5288553), (13.3032103, 52.529038), (13.3015366, 52.5292599), (13.2999058, 52.5294949), (13.29879, 52.5295602),
                    (13.2975884, 52.5294819), (13.2964941, 52.5293383), (13.2828255, 52.5286203), (13.2822032, 52.5275107), (13.2817312, 52.5265316), (13.2814522, 52.5255655), (13.2811089, 52.52426), (13.2813879, 52.5228761), (13.2816883, 52.5218316), (13.2823534, 52.5203302), (13.2831259, 52.5186197), (13.2835336, 52.5176535), (13.284113, 52.5168439), (13.2852931, 52.515956), (13.2858725, 52.5154467), (13.2865377, 52.5144151), (13.2865162, 52.5135141), (13.2864304, 52.5124563), (13.2860656, 52.5111504), (13.2855292, 52.5100796), (13.2847138, 52.5089172), (13.2838984, 52.5076373), (13.2831903, 52.5065664), (13.2828041, 52.5055607), (13.2828041, 52.5046987), (13.2825466, 52.5039542), (13.2818814, 52.5032489), 
                    (13.2804652, 52.5019819), (13.2800789, 52.5011851), (13.2802077, 52.5003752), (13.2810016, 52.4993171), (13.2821603, 52.4980239), (13.2834263, 52.4969266), (13.284585, 52.4955549), (13.2860656, 52.4945881), (13.2868166, 52.4943007), (13.2889195, 52.4941309), (13.2905717, 52.4939741), (13.2916232, 52.4934515), (13.2943268, 52.4919752), (13.2966443, 52.4906164), (13.2988115, 52.4890878), (13.3005925, 52.4878726), (13.3046051, 52.4846974), (13.3062788, 52.4833776),
                    (13.3073087, 52.4828026), (13.309197, 52.4821623), (13.3103128, 52.481718), (13.3123513, 52.4803981), (13.3143468, 52.4794441), (13.3175869, 52.4784117), (13.321385, 52.4779412), (13.3259125, 52.4779281), (13.3302255, 52.4779281), (13.3321138, 52.4779804), (13.3346887, 52.478281), (13.3373495, 52.4786208), (13.3404394, 52.4787645), (13.3419629, 52.4787384), (13.3435936, 52.4785685), (13.3441945, 52.478281), (13.3451815, 52.4777843), (13.3470054, 52.476582), (13.3485933, 52.4756671), (13.3494516, 52.475275), (13.3508893, 52.4755887), (13.3523484, 52.4758762), (13.3531209, 52.4762422), (13.353786, 52.4768826), (13.3543225, 52.4774968), (13.3550306, 52.478098), (13.3553954, 52.4780849), 
                    (13.3572407, 52.4767519), (13.3584209, 52.4761376), (13.3602019, 52.4753273), (13.3616062, 52.4746066), (13.3637209, 52.4741248), (13.3655448, 52.4732752), (13.3668538, 52.4726609), (13.3678194, 52.4720335), (13.3691283, 52.471393), (13.3716174, 52.4708048), (13.375587, 52.4702166), (13.3792563, 52.4700206), (13.3833762, 52.4698898), (13.3865948, 52.4697461), (13.3883543, 52.46955), (13.3907576, 52.4690663), (13.392324, 52.468465), (13.393869, 52.4677722), (13.3963795, 52.4667133),
                    (13.3987828, 52.4659421), (13.4014864, 52.4651315), (13.4029885, 52.4640857), (13.4041901, 52.4630529), (13.4059926, 52.4621508), (13.4081598, 52.4617194), (13.4130736, 52.4609088), (13.4178157, 52.4607127), (13.4196826, 52.4611703), (13.4204336, 52.4617455), (13.4240599, 52.4635105), (13.4327717, 52.4646348), (13.4333725, 52.4649616), (13.4356256, 52.4668571), (13.4420844, 52.4676676), (13.4484573, 52.4683997), (13.4540577, 52.4691317), (13.4527703, 52.4703996), (13.4521695, 52.4710924), (13.4530921, 52.47138), (13.4540148, 52.471942), (13.4551735, 52.4728178), (13.4558602, 52.4738634), (13.4582205, 52.4727132), (13.4586282, 52.474347), (13.4593363, 52.4777974), 
                    (13.4588428, 52.4778497), (13.4591861, 52.4794702), (13.4599801, 52.4826981), (13.4600873, 52.4836782), (13.460023, 52.4840833), (13.4597011, 52.4843969), (13.4598513, 52.4847889), (13.4592076, 52.4852332), (13.4586711, 52.485586), (13.4598728, 52.4902898), (13.4594222, 52.4905642), (13.4577055, 52.4916747), (13.4578557, 52.4920275), (13.460774, 52.4941178), (13.4633704, 52.4963387), (13.4645643, 52.4974174), (13.4654821, 52.4971273), (13.4660633, 52.4968548), (13.4674795, 52.497939), (13.4678336, 52.4985072),
                    (13.4681858, 52.4993089), (13.4683145, 52.4996224), (13.4687008, 52.4996485), (13.4687437, 52.4998314), (13.4686579, 52.5000926), (13.4688099, 52.5007736), (13.4691103, 52.501492), (13.4696038, 52.502341), (13.4698399, 52.502328), (13.4700759, 52.5030986), (13.4693571, 52.5031835)]
    }

tel_aviv = {
        "country": "Israel",
        "city": "Tel Aviv",
        "polygon": [(34.775838, 32.1030508), (34.7701732, 32.0968887), (34.7663108, 32.0880357), (34.7657958, 32.0794908), (34.7642938, 32.0776181), (34.7607318, 32.0697087), (34.7595945, 32.0660538), (34.753286, 32.0564522), (34.7490588, 32.0555792), (34.7478566, 32.0512504), (34.7531137, 32.0500682), (34.7589288, 32.0496317), (34.7617612, 32.0495953), (34.7656879, 32.0476675), (34.7686276, 32.0446119), (34.7780046, 32.0388278), (34.7802362, 32.0400465), (34.782897, 32.0436661), (34.7841844, 32.0490679), (34.7842595, 32.0504592), (34.7839913, 32.051996), (34.7843561, 32.0552332), 
                    (34.7849124, 32.056933), (34.7860711, 32.0594426), (34.7884529, 32.0634797), (34.7903412, 32.0660073), (34.7922079, 32.0688985), (34.7926157, 32.0724078), (34.793445, 32.0743626), (34.7943381, 32.0762695), (34.7956669, 32.0783613), (34.7965091, 32.0796886), (34.7967076, 32.0809794), (34.7972763, 32.0829793), (34.7989929, 32.0868699), (34.800216, 32.0912875), (34.8010635, 32.0953503), (34.8019111, 32.0994131), (34.788779, 32.0967229), (34.7793806, 32.0960503), (34.7774923, 32.0972864), (34.777621, 32.0991587), (34.7777498, 32.10114), (34.775838, 32.1030508)]
    }

jerusalem = {
        "country": "Israel",
        "city": "WestJerusalem",
        "polygon": [(35.1817982, 31.7716133), (35.1801823, 31.7690279), (35.176277, 31.7691009), (35.1740883, 31.7681887), (35.1743458, 31.765963), (35.1731012, 31.7635914), (35.1723288, 31.7619859), (35.1747749, 31.7612196), (35.1763003, 31.7617966), (35.1840876, 31.7554542), (35.1887653, 31.7542865), (35.1934002, 31.7565125), (35.197472, 31.7574317), (35.1997517, 31.754177), 
                    (35.2008246, 31.7520605), (35.2047728, 31.7507103), (35.205674, 31.7489951), (35.2083347, 31.7512212), (35.2149008, 31.7506373), (35.2190636, 31.7497615), (35.225458, 31.7623873), (35.226445, 31.7686265), (35.2255867, 31.7705603), (35.2266167, 31.7714724), (35.2273033, 31.7763247), (35.2255009, 31.7784407), (35.2250413, 31.7789474), (35.2278523, 31.7806164), (35.2280025, 31.7817382), (35.2271656, 31.7834528), (35.2272407, 31.7861522), (35.2265112, 31.7925176), (35.2265594, 31.7933976), (35.2232764, 31.7942183), (35.2216242, 31.7936347), 
                    (35.2198646, 31.7956043), (35.2152225, 31.7936072), (35.2118609, 31.7921391), (35.2089856, 31.792431), (35.2044278, 31.7923225), (35.2030115, 31.7910093), (35.2009731, 31.7907722), (35.1996133, 31.7893066), (35.1999968, 31.7878228), (35.1954584, 31.7833671), (35.1901155, 31.7826922), (35.1869949, 31.7788226), (35.1844951, 31.7763532), (35.1817982, 31.7716133)]
    }

country_array = [tel_aviv, berlin, hamburg, jerusalem]

model = tf.keras.models.load_model(PATH / "my_model")

@api.post("/predict")
def predict(file: UploadFile = File(...)):
    image = load_image(file)
    pre_image = preprocess(image)
    prediction_id = uuid.uuid4()
    label = predict_image(pre_image, model)
    return {
        "prediction_id": prediction_id,
        "class_label": label,
    }


# Explain Prediction
@api.post("/explain")
async def explain_api(file: UploadFile = File(...)):
    image = load_image(file)
    pre_image = preprocess(image)

    explanation = explain_cnn(pre_image, model)
    explain_id = uuid.uuid4()
    encoded_image_string = convert_explanation(explanation)
    encoded_bytes = bytes("data:image/png;base64,",
                          encoding="utf-8") + encoded_image_string

    return {
        "image": encoded_bytes,
        "explain_id": explain_id
    }


@api.get("/msg")
def home():
    return {
        "data": "Was this Google Streetview photo taken in Tel-Aviv or Berlin? Challenge yourself with an AI."
    }


@api.get("/streetview")
def streetview():

    nominated_country = random.randint(0, 3)
    coordinaten = country_array[nominated_country]['polygon']
    poly = Polygon(coordinaten)
    imagery_hits = 0
    status = False
    while imagery_hits < 1:
        while status != "OK":
            coord = generate_random(poly)
            lng = coord[0][0]
            lat = coord[0][1]
            locstring = str(lat) + "," + str(lng)
            r = requests.get(API_URL + "?key=" + API_KEY +
                             "&location=" + locstring + "&source=outdoor")
            status = r.json()["status"]
            print(status)
        print("    ========== Got one! ==========")
        url = GOOGLE_URL + "&location=" + locstring
        try:
            contents = urlopen(url).read()
            #urlretrieve(url, outfile)
        except URLError:
            #print("    No imagery")
            break

        imagery_hits += 1
        status = False
        encoded_image_string = base64.b64encode(contents)
        encoded_bytes = bytes("data:image/png;base64,",
                              encoding="utf-8") + encoded_image_string
    return {
        "image": encoded_bytes,
        "class_label": country_array[nominated_country]['city']
    }
