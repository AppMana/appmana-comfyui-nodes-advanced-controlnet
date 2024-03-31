from torch import Tensor

from nodes import VAEEncode
import comfy.utils
from comfy.sd import VAE

from .control_reference import ReferenceAdvanced, ReferenceOptions, ReferenceType, ReferencePreprocWrapper


# node for ReferenceCN
class ReferenceControlNetNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "reference_type": (ReferenceType._LIST,),
                "style_fidelity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "ref_weight": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }
    
    RETURN_TYPES = ("CONTROL_NET", )
    FUNCTION = "load_controlnet"

    CATEGORY = "Adv-ControlNet 🛂🅐🅒🅝/Reference"

    def load_controlnet(self, reference_type: str, style_fidelity: float, ref_weight: float):
        ref_opts = ReferenceOptions(reference_type=reference_type, style_fidelity=style_fidelity, ref_weight=ref_weight)
        controlnet = ReferenceAdvanced(ref_opts=ref_opts, timestep_keyframes=None)
        return (controlnet,)


class ReferencePreprocessorNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", ),
                "vae": ("VAE", ),
                "latent_size": ("LATENT", ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("proc_IMAGE",)
    FUNCTION = "preprocess_images"

    CATEGORY = "Adv-ControlNet 🛂🅐🅒🅝/Reference/preprocess"

    def preprocess_images(self, vae: VAE, image: Tensor, latent_size: Tensor):
        # first, resize image to match latents
        image = image.movedim(-1,1)
        image = comfy.utils.common_upscale(image, latent_size["samples"].shape[3] * 8, latent_size["samples"].shape[2] * 8, 'nearest-exact', "center")
        image = image.movedim(1,-1)
        # then, vae encode
        try:
            image = vae.vae_encode_crop_pixels(image)
        except Exception:
            image = VAEEncode.vae_encode_crop_pixels(image)
        encoded = vae.encode(image[:,:,:,:3])
        return (ReferencePreprocWrapper(condhint=encoded),)
