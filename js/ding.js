var CryptoJS = require("crypto-js");
var Base64 = require('js-base64').Base64;

function decrypt(word,key){
    word = Base64.decode(word)
    var key = CryptoJS.MD5(key)
    function Decrypt(word) {
        let decrypted = CryptoJS.AES.decrypt(word, key, { iv: [], mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.Pkcs7 });
        return decrypted.toString(CryptoJS.enc.Utf8);
    }
    var result = Decrypt(word)
    return result
}

function encrypt(form){
    var key = CryptoJS.MD5("zntb666666666666")
    function Encrypt(word) {
        let toSec = CryptoJS.enc.Utf8.parse(word)
        let encrypted = CryptoJS.AES.encrypt(toSec, key, { iv: [], mode: CryptoJS.mode.ECB, padding: CryptoJS.pad.Pkcs7 });
        return encrypted.toString();
    }
    
    var result = Encrypt(JSON.stringify(form))
    var toBase64 = Base64.encode(result)
    return toBase64
}