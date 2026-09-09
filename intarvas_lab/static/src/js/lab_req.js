// TEMPORARILY DISABLED TO PREVENT ERRORS
/*
odoo.define('intarvas_lab.lab_req.js', function (require) {
"use strict";

    var config = require('web.config');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var utils = require('web.utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;


    $(document).ready(function() {

           var result = document.querySelector('#lab_test_total');
           var lab_tests = document.getElementsByClassName('lab_test_ids');

                $('#test_charge').hide();
                $(".lab_test_ids").change(function (e) {

                 if($('#lab_test_total').val() == ' '){
                        console.log("=================22========================================")
                        $('#test_charge').hide();
                 }else{
                        console.log("=================2555555========================================")
                        $('#test_charge').show();
                 }

                    var lst = []
                    Array.from(lab_tests).forEach(function (n) {
                        if(n.checked == true){
                            lst.push(n.value)
                        }
                    });
                var input_val = this.value
                    var res = rpc.query({
                        model: 'oeh.medical.labtest.types',
                        method: 'search_read',
                        fields :['id','name','test_charge'],
                        domain: [['id', '=', lst]],
                        }).then(function (e) {
                          var total = 0.0;
                          for(var prod in e){
                                var prods = e[prod]
                                     total =  total + prods.test_charge
                                     if(result) {
                                         result.textContent = total
                                     }
                                }
                            })
                    })


    });

});
*/
