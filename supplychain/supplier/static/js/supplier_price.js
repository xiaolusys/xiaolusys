function calcSalePrice(cost){
    var salePrice = NaN;
    if(!isNaN(cost)){
        var onSalePrice = Math.round(parseFloat(cost) / .65 + 8);
        var onSalePriceStr = String(onSalePrice);
        var lastDigit = parseInt(onSalePriceStr[onSalePriceStr.length - 1]);
        if(lastDigit < 5)
            salePrice = Math.max(Math.floor(onSalePrice / 10) - 1, 0) * 10 + 9.9;
        else
            salePrice = Math.floor(onSalePrice / 10) * 10 + 9.9;
        // (9.9, 39.9]区间内的销售价统一改成39.9
        if(salePrice > 9.9  && salePrice <= 39.9)
            salePrice = 39.9;
        // (99.9, 109.9]区间内的销售价统一改成109.9
        if(salePrice > 99.9 && salePrice <= 109.9)
            salePrice = 99.9;
    }
    return salePrice;
}
