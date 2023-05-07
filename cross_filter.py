# -*- coding: utf-8 -*-

####################
# import
####################
# gimpfu用
from gimpfu import *

# ファイル入出力用
import sys

####################
# parameters
####################

# --verboseなら%USER_PROFILE%のパス、
# 通常起動なら.xcfファイルがあるパスに出力される
OUTTXT_PATH = "stdout.txt"
PW = 10
PH = 10

####################
# method
####################

def hello_world(message, image, drawable):
    # verboseモードだとコンソールに出力され、
    # 通常モードだとエラーメッセージボックスとして表示される。
    # messageには呼び出し時にhello worldを渡している。
    gimp.message("Message: " + message)

    # ファイル書き出し用
    sys.stdout = open(OUTTXT_PATH, 'w')

    # ファイルにピクセル値を書き出し
    w = min(PW, drawable.width)
    h = min(PH, drawable.height)
    src_rgn = drawable.get_pixel_rgn(0, 0, w, h, False, False)
    for x in xrange(0, w):
        for y in xrange(0, h):
            p = map(ord, src_rgn[x, y])
            print x, ":", y, " -- ", "".join(map((lambda x: format(x, '02x')), p))


# spline曲線を256点のポイントにして返すメソッド
def spline_to_points(spline):
    points = [ k/255.0 for k in range(256) ]
    x0 = 0.0
    y0 = 0.0
    ix = 0
    x0 = spline.pop(0) # remove initial (0.0,0.0)
    y0 = spline.pop(0)
    while spline:
        x = spline.pop(0)
        y = spline.pop(0)
        while ix < 256:
            xi = ix / 255.
            if xi > x:
                break
            points[ix] = ((x-xi) * y0 + (xi-x0) * y) / (x-x0)
            ix += 1

        x0 = x
        y0 = y
    return points


def cross_filter_core(image, drawable):

    kobo = 4 # 光芒の数の半分、光芒は偶数のみ可能

    mblur_type = 0      # リニアモーション
    mblur_length1 = 5   # length(1回目)
    mblur_length2 = 10  # length(2回目)
    angle_offset  = 0   # angle offset
    mblur_cx = 5        # center x
    mblur_cy = 2        # center y
    gauss_h = 3         # gauss h
    gauss_v = 3         # gauss v

    # レイヤーグループを追加
    layer_group = pdb.gimp_layer_group_new(image)
    pdb.gimp_image_insert_layer(image, layer_group, None, 0)

    angle = angle_offset
    angle_dx = 360 / (kobo * 2)
    for n in range(kobo):

        # レイヤーをコピー
        work_layer = pdb.gimp_layer_copy(drawable, 1)  # alphaチャンネルを追加
        pdb.gimp_image_insert_layer(image, work_layer, layer_group, 0) # レイヤーグループに追加

        # 角度を更新
        angle += angle_dx

        # ガウスフィルタIIR処理実行
        # pdb.plug_in_gauss(image, work_layer, gauss_h, gauss_v, 0) # 0: IIR

        # モーションぼかし処理実行
        pdb.plug_in_mblur(image, work_layer, mblur_type, mblur_length1, angle, mblur_cx, mblur_cy)
        pdb.plug_in_mblur(image, work_layer, mblur_type, mblur_length2, angle, mblur_cx, mblur_cy)

        # アルファチャンネル調整
        points = spline_to_points([0.0, 0.0, 0.2, 0.8])
        pdb.gimp_drawable_curves_explicit(work_layer, HISTOGRAM_ALPHA, 256, points)

    # レイヤーのマージ
    dst_layer = pdb.gimp_image_merge_layer_group(image, layer_group)
    dst_layer.name = "cross_filter"

def cross_filter(image, drawable):

    try:
        # 処理開始
        gimp.progress_init("Discolouring " + drawable.name + "...")

        # undoグループ開始
        pdb.gimp_image_undo_group_start(image)


        # クロスフィルタの実体
        cross_filter_core(image, drawable)

    finally:
        # undoグループ終了
        pdb.gimp_image_undo_group_end(image)

        # 処理終了
        pdb.gimp_progress_end()


# 引数はregisterで登録するときに指定する。
# message: PF_STRING
# image: PF_IMAGE
# drawable: PF_DRAWABLE
def plugin_main(message, image, drawable):

    # hello_world実行
    # hello_world(message, image, drawable)

    # cross_filter実行
    cross_filter(image, drawable)



####################
# スクリプト登録
####################
# メニューバーの Filters > My にスクリプトを追加

prms = [
    (PF_STRING, "string", "Text string", 'Hello, world!'),
    (PF_IMAGE, "image",       "Input image", None),
    (PF_DRAWABLE, "drawable", "Input drawable", None)
    ]
register(
    "cross_filter",             # name
    "my cross filter",          # blurb (宣伝文句),
    "help: this is my filter",  # help
    "skattun",                  # author
    "(C) 2023 skattun",         # copyright
    "2023/5/5",                 # date
    "cross_filter",             # menupath(not use)
    "RGB*",                     # imagetypes
    prms,                       # params
    [],                         # results
    plugin_main,                # function
    menu = "<Image>/Script-Fu/My")# menu path設定

####################
# main
####################
main()
