from ssg.reformat_html import revert_html_ampersand_char_codes


def test_revert_html_ampersand_char_codes():
    source = """
        &#39; '  &acute; ´  &aelig; æ  &AElig; Æ  &amp; &  &Aring; Å  &brvbar; ¦
        &ccedil; ç  &Ccedil; Ç  &cedil; ¸  &cent; ¢  &copy; ©  &curren; ¤  &deg; °
        &divide; ÷  &eth; ð  &ETH; Ð  &frac12; ½  &frac14; ¼  &frac34; ¾  &gt; >
        &iexcl; ¡  &iquest; ¿  &laquo; «  &lt; <  &macr; ¯  &micro; µ  &middot; ·
        &nbsp; u  &not; ¬  &ntilde; ñ  &Ntilde; Ñ  &oelig; œ  &OElig; Œ  &ordf; ª
        &ordm; º  &Oslash; Ø  &para; ¶  &plusmn; ±  &pound; £  &quot; "  &raquo; »
        &reg; ®  &sect; §  &shy; ­  &sup1; ¹  &sup2; ²  &sup3; ³  &szlig; ß
        &thorn; þ  &THORN; Þ  &times; ×  &uml; ¨  &yen; ¥
        """
    expected = """
        ' '  ´ ´  æ æ  Æ Æ  & &  Å Å  ¦ ¦
        ç ç  Ç Ç  ¸ ¸  ¢ ¢  © ©  ¤ ¤  ° °
        ÷ ÷  ð ð  Ð Ð  ½ ½  ¼ ¼  ¾ ¾  > >
        ¡ ¡  ¿ ¿  « «  < <  ¯ ¯  µ µ  · ·
        u u  ¬ ¬  ñ ñ  Ñ Ñ  œ œ  Œ Œ  ª ª
        º º  Ø Ø  ¶ ¶  ± ±  £ £  " "  » »
        ® ®  § §  ­ ­  ¹ ¹  ² ²  ³ ³  ß ß
        þ þ  Þ Þ  × ×  ¨ ¨  ¥ ¥
        """
    assert revert_html_ampersand_char_codes(source) == expected
