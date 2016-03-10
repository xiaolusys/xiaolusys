/**
 * Created by jishu_linjie on 12/8/15.
 */

function fill_select_option(total_material, select_dom) {
    var value = 0;
    $(select_dom).empty();
    $.each(total_material, function (index, sub_arry) {
        $.each(sub_arry, function (i, v) {
            var option = '<option value="' + v + '">' + v + '</option>';
            value += 1;
            $(select_dom).append(option);
        });
    });
}

function select_to_input(select_id, input_id, input_id2) {

    var select_dom = $("#" + select_id);
    var input_dom = $("#" + input_id);
    var input_dom2 = $("#" + input_id2);

    // 材质数组
    var null_material = [''];
    var material_baffeta = ['棉织物'];
    var material_fibre = ['棉麻织物'];
    var material_silk = ['真丝', '雪纺', '蕾丝', '丝绒织物'];
    var material_chemical_fiber = ['聚酯纤维', '化纤织物'];
    var material_jean = ['牛仔织物'];
    var material_feather = ['羽绒制品'];
    var material_wool = ['羊毛', '羊绒', '貂绒', '马海毛'];
    var material_leather = ['PU', '人造皮', '绒面皮', '磨砂皮', '翻毛皮', '油光皮革制品'];
    var material_modaier = ['莫代尔'];//注册材质类别

    var total_material = [null_material, material_baffeta, material_fibre, material_silk, material_chemical_fiber, material_jean,
        material_feather, material_wool, material_leather, material_modaier];
    // 填充 option
    fill_select_option(total_material, select_dom);
    var Washing_instructions = {// 注册材质洗涤说明
        baffeta: "洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度， 不可漂白。有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。(如是婴幼儿衣物，请于成人衣物分开洗涤，避免交叉感染。建议手洗水温30度，使用婴幼儿专用衣物洗涤剂。）",
        fibre: "洗涤时请深色、浅色衣物分开洗涤。不宜浸泡，冷水洗涤。使用中性洗涤剂或用洗衣液，如：丝麻洗涤剂等 禁止使用氯、酶洗涤用品。禁止暴晒，平置晾干。",
        silk: "洗涤时请深色、浅色衣物分开洗涤 。使用中性洗涤剂或专用洗衣液。采用冷水手洗，避免机洗，浸泡时间不宜过长。忌碱性洗涤剂，应选用中性或丝绸专用洗涤剂。禁止暴晒，自然阴干。",
        chemical_fiber: "洗涤时请深色、浅色衣物分开洗涤。30度水洗，不可漂白，悬挂晾干，不可干洗。",
        jean: "最高洗涤温度为30度。不可漂白，悬挂晾干。分开洗涤，不可浸泡，深色牛仔会伴有正常性脱色。",
        feather: "最高手洗温度为30度，使用中性洗涤剂，不能拧干，平铺晾干，勿暴晒、熨烫。",
        wool: "最高手洗温度为30度，翻面洗涤，减少摩擦，避免起球。使用中性洗涤剂，平铺晾干，勿暴晒、熨烫。",
        leather: "沾水及洗涤剂进行清洗，不能干洗。勿暴晒，勿接触有机溶剂。",
        modaier: "水洗时要随洗随浸，浸泡时间不可超过15分钟，洗涤液温度不能超过35度。粘胶纤维织物遇水会发硬，纤维结构很不牢固，洗涤时要轻洗，以免起毛或裂口."
    };//洗涤说明

    $(select_dom).change(function () {
        var select = $(select_dom).val();
        var instruction = map_instructions(select);
        $(input_dom).val(instruction);
        $(input_dom2).val(select);
    });

    function map_instructions(select) { // 返回洗涤说明
        var instruction = '';
        if ($.inArray(select, material_baffeta) >= 0) {
            instruction = Washing_instructions.baffeta;
        }
        if ($.inArray(select, material_fibre) >= 0) {
            instruction = Washing_instructions.fibre;
        }
        if ($.inArray(select, material_silk) >= 0) {
            instruction = Washing_instructions.silk;
        }
        if ($.inArray(select, material_chemical_fiber) >= 0) {
            instruction = Washing_instructions.chemical_fiber;
        }
        if ($.inArray(select, material_jean) >= 0) {
            instruction = Washing_instructions.jean;
        }
        if ($.inArray(select, material_feather) >= 0) {
            instruction = Washing_instructions.feather;
        }
        if ($.inArray(select, material_wool) >= 0) {
            instruction = Washing_instructions.wool;
        }
        if ($.inArray(select, material_leather) >= 0) {
            instruction = Washing_instructions.leather;
        }
        if ($.inArray(select, material_modaier) >= 0) {
            instruction = Washing_instructions.modaier;
        }
        return instruction
    }
}

function choose_2_input(select_id, input_id, input_id2) {
    console.log("washing is running");
    select_to_input(select_id, input_id, input_id2)
}

