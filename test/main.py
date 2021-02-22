from src.MetaReporter import MetaReporter

model_path_1 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw1"
result_path_1 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw1"

model_path_2 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw4_AdaBound"
result_path_2 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw4_AdaBound"

model_path_3 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw4_Adam"
result_path_3 = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11\\S11_LNRN18s_new_nt_bw4_Adam"

session_path = "D:\\Karriere\\KestrelEye\\MetaReporter\\reports\\session11"

config_path = "D:\\Karriere\\KestrelEye\\MetaReporter\\src\\config\\config.json"

# meta_reporter_1 = MetaReporter(model_path_1, result_path_1, config_path=config_path, level=0)
# print(meta_reporter_1)

# meta_reporter_2 = MetaReporter(model_path_2, result_path_2, config_path=config_path, level=0)
# print(meta_reporter_2)

# meta_reporter_3 = MetaReporter(model_path_3, result_path_3, config_path=config_path, level=0)
# print(meta_reporter_3)

meta_reporter_session = MetaReporter(session_path, session_path, config_path, level=1)
print(meta_reporter_session)
