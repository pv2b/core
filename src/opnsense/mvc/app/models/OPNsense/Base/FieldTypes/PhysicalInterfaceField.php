<?php

/**
 *    Copyright (C) 2016 IT-assistans Sverige AB
 *    Copyright (C) 2014-2016 Deciso B.V.
 *    Copyright (C) 2003-2004 Manuel Kasper <mk@neon1.net>
 *
 *    All rights reserved.
 *
 *    Redistribution and use in source and binary forms, with or without
 *    modification, are permitted provided that the following conditions are met:
 *
 *    1. Redistributions of source code must retain the above copyright notice,
 *       this list of conditions and the following disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *
 *    THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
 *    INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 *    AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *    AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 *    OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 *    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 *    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 *    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 *    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *    POSSIBILITY OF SUCH DAMAGE.
 *
 */
namespace OPNsense\Base\FieldTypes;

use Phalcon\Validation\Validator\InclusionIn;

require_once("interfaces.inc");
require_once("util.inc");

/**
 * Class PhysicalInterfaceField field type to select physical interfaces
 * @package OPNsense\Base\FieldTypes
 */
class PhysicalInterfaceField extends BaseField
{
    /**
     * @var bool marks if this is a data node or a container
     */
    protected $internalIsContainer = false;

    /**
     * @var string default validation message string
     */
    protected $internalValidationMessage = "please specify a valid physical interface";

    /**
     * @var array collected options
     */
    private static $internalOptionList = array();

    /**
     * @var include LAGG interfaces
     */
    private $includeLAGGInterfaces = true;

    /**
     * @var include jumbo capable (and also VLAN capable) interfaces
     */
    private $jumboCapableOnly = false;

    /**
     * generate validation data (list of potential physical interfaces)
     */
    public function eventPostLoading()
    {
        if (count(self::$internalOptionList) == 0) {
            /* This logic adapted from src/www/interfaces_vlan_edit.php in the
               legacy code.
               FIXME This should probably be cleaned up, especially the LAGG
               code is hairy and won't work after that is moved to the new
               model. Also this logic might actually belong in a different
               class? */
            $portlist = get_interface_list();
            /* add LAGG interfaces */
            if ($this->includeLAGGInterfaces && isset($config['laggs']['lagg'])) {
                foreach ($config['laggs']['lagg'] as $lagg) {
                    $portlist[$lagg['laggif']] = $lagg;
                }
            }
            foreach ($portlist as $ifn => $ifinfo) {
                if ($this->jumboCapableOnly && !is_jumbo_capable($ifn)) {
                    continue;
                }
                $desc = $ifn;
                if (!empty($ifinfo['mac'])) {
                    $desc .= " (" . $ifinfo['mac'] . ")";
                }
                self::$internalOptionList[$ifn] = $desc;
            }
        }
    }

    /**
     * get valid options, descriptions and selected value
     * @return array
     */
    public function getNodeData()
    {
        $result = array();
        foreach (self::$internalOptionList as $optKey => $optValue) {
            if ($optKey == $this->internalValue) {
                $selected = 1;
            } else {
                $selected = 0;
            }
            $result[$optKey] = array("value" => $optValue, "selected" => $selected);
        }

        return $result;
    }

    /**
     * retrieve field validators for this field type
     * @return array returns validators
     */
    public function getValidators()
    {
        $validators = parent::getValidators();
        if ($this->internalValue != null) {
            $validators[] = new InclusionIn(array('message' => $this->internalValidationMessage,
                'domain'=>array_keys(self::$internalOptionList)));
        }
        return $validators;
    }

    /**
     * select if LAGG interfaces are to be included
     * @param string $value boolean value Y/N
     */
    public function setIncludeLAGGInterfaces($value)
    {
        if (trim(strtoupper($value)) == "Y") {
            $this->includeLAGGInterfaces = true;
        } else {
            $this->includeLAGGInterfaces = false;
        }
    }

    /**
     * select if only jumbo capable interfaces are to be included
     * @param string $value boolean value Y/N
     */
    public function setJumboCapableOnly($value)
    {
        if (trim(strtoupper($value)) == "Y") {
            $this->jumboCapableOnly = true;
        } else {
            $this->jumboCapableOnly = false;
        }
    }
}
