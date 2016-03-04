

from pylon import puts
# import re
import os

# import time
# from pylon import datalines
import pylon

from filler import Filler
from infotext import InfoText





class Documasonry:
  """docstring for Documasonry

  yaml basic config
  GUI
  如果某个模板被打开且编辑了部分字段怎么办
  - Word 和 Excel 会使用编辑中的模板, 输出包含编辑部分的成果
  - AutoCAD 会开新的只读实例, 按照原模板输出成果

  AutoCAD 特殊 field
    - insert block {{地形}} to back layer
    - 位置校正
      原始模板在(0, 0)处 需要调整到界址线图形所在位置
      polygon边框确定:
        参数 padding比例, 是否方形
        先定位中心 c, 边界框 w, h
        padding = max(w, h) * padding_ratio
        方形 ? 边界框长边 + padding : 边界框长边短边分别 + padding


  yaml_text = '''
              项目名称: test1
              单位名称: test2
              地籍号: 110123122
              name: sjgisdgd
              面积90: 124.1
              面积80: 234.2
              zdfile: zd.dwg
              地形file: dx.dwg  # relative path for output_folder
              日期: today
              '''

  """
  def __init__(self, output_path='', template_paths=[]):
    self.output_path = output_path
    self.template_paths = template_paths


  def set_output_path(self, path):
    self.output_path = path

  def set_template_paths(self, paths):
    self.template_paths = paths

  def read_templates_from_config(self, only_selected=True):
    default_templates = self.read_config()['default_templates']
    if only_selected:
      return [item['file'] for item in default_templates if item['selected']]
    else:
      return [item['file'] for item in default_templates]

  def generate(self, info, save=True, add_index=True):
    for i, tmpl in enumerate(self.template_paths, 1):
      filler = Filler(template_path=tmpl, output_folder=self.output_path)
      filler.render(info=info)
      if save:
        prefix = '{:02d}-'.format(i) if add_index else ''
        filler.save(info=info, close=True, prefix=prefix)

  def detect_required_fields(self, quick=False):
    '''quick=Ture -> preview required_fields from config.yaml
       quick=False -> detect from open tmpl files and check by string "{{*}}
    '''
    field_names = []
    if quick:
      default_templates = self.read_config()['default_templates']
      for tmpl in self.template_paths:
        found = [item for item in default_templates if item['file'] == tmpl]
        if found and found[-1].get('required_fields'):
          field_names.extend(found[-1]['required_fields'])
    else:
      for tmpl in self.template_paths:
        filler = Filler(template_path=tmpl, output_folder=self.output_path)
        field_names.extend(filler.detect_required_fields(close=True, unique=True))
    return list(pylon.dedupe(field_names))


  def generate_required_fields_info_text(self, quick=False):

    fields = self.detect_required_fields(quick=quick)
    text = '\n'
    for field in fields:
      text += '{}: \n'.format(field)
    if quick:
      text += '\n'
    else:
      text += '\n# generated by reading template files\n'
    return text


  def combine_fields_info_text(self, info1_text, info2_text):
    # result = ''
    info1 = InfoText.from_string(info1_text)
    info2 = InfoText.from_string(info2_text)
    info1.merge(info2)
    return info1.to_yaml_string()



  def read_config(self):
    '''config.yaml

    default_templates:
      - file: 'abspath/to/template1'
        selected: true
        required_fields: ['field1', 'field2', 'field3']
      - file: 'abspath/to/template2'
        selected: true
      - file: 'abspath/to/template3'
        selected: false
        required_fields: ['field1', 'field2', 'field3']

    required_fields 如不配置, 则需要用 filler.detect_required_fields() 检测出
    '''
    path = os.getcwd() + '/config.yaml'
    config = InfoText.from_yaml(path).content
    # config | puts(max_depth=10)
    for i, item in enumerate(config['default_templates']):
      file_path = item['file']
      if not os.path.isfile(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
        if os.path.isfile(file_path):
          config['default_templates'][i]['file'] = file_path
    return config


















def test_documasonry_detect_fields():
  template_paths = [os.getcwd() + '/test/test_templates/_test_{{项目名称}}-申请表.xls',
                    os.getcwd() + '/test/test_templates/test_{{name}}_面积计算表.doc',
                    os.getcwd() + '/test/test_templates/test_{{测试单位}}-宗地图.dwg',
                    os.getcwd() + '/test/test_templates/test_no_field_面积计算表.doc',
                    ]
  output_path = os.getcwd() + '/test/test_output'
  masonry = Documasonry(output_path=output_path, template_paths=template_paths)
  masonry.detect_required_fields() | puts()
  # [项目名称, 单位名称, 地籍号, name, 面积90, 面积80, area, 测试单位, title, project, date, ratio, landcode, area80, area90] <-- list length 15






def test_documasonry_generate():
  template_paths = [os.getcwd() + '/test/test_templates/_test_{{项目名称}}-申请表.xls',
                    os.getcwd() + '/test/test_templates/test_{{name}}_面积计算表.doc',
                    os.getcwd() + '/test/test_templates/test_{{测试单位}}-宗地图.dwg',
                    os.getcwd() + '/test/test_templates/test_no_field_面积计算表.doc',
                    ]
  output_path = os.getcwd() + '/test/test_output'
  masonry = Documasonry(output_path=output_path, template_paths=template_paths)
  text = '''
         项目名称: test1
         单位名称: test2
         地籍号: 110123122
         name: sjgisdgd
         面积90: 124.1
         面积80: 234.2
         area: 124.2
         测试单位: testconm
         title: testtitle
         project: pro.
         date: 20124002
         ratio: 2000
         landcode: 235
         area80: 94923
         area90: 3257
         '''
  info = InfoText.from_string(text)
  masonry.generate(info=info, save=True, add_index=True) | puts()









def test_load_config():
  masonry = Documasonry(output_path=1, template_paths=[])
  masonry.read_config()
  masonry.read_templates_from_config()
  # masonry.generate_required_fields_info_text(quick=True) | puts()
  # masonry.generate_required_fields_info_text(quick=False) | puts()


def test_detect_fields():
  masonry = Documasonry()
  masonry.set_template_paths(paths=masonry.read_templates_from_config())
  masonry.set_output_path(path='')
  masonry.generate_required_fields_info_text(quick=True) | puts()
  pass


def test_combine_fields_info_text():
  info1_text = '''
    项目名称: org
    单位名称:
    code: 110123122

  '''
  info2_text = '''
    项目名称: new
    单位名称: name
    code:
    area: 124.2
  '''

  d = Documasonry()
  r = d.combine_fields_info_text(info1_text, info2_text)
  puts('----')
  puts(r)


  info1_text = '''

  '''
  info2_text = '''
    项目名称: test1
    单位名称:
    地籍号: 110123122
    name: sjgisdgd
    面积90: 124.1
    面积80: 234.2
    area: 124.2
  '''

  d = Documasonry()
  r = d.combine_fields_info_text(info1_text, info2_text)
  puts('----')
  puts(r)


  info1_text = '''
    面积90: 20.1
    项目名称:
    单位名称:
    面积80:
  '''
  info2_text = '''

  '''

  d = Documasonry()
  r = d.combine_fields_info_text(info1_text, info2_text)
  puts('----')
  puts(r)
