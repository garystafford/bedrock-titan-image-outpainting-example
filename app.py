# Image Background Replacement on Amazon Bedrock using outpainting
# Author: Gary A. Stafford
# Date: 2024-08-20

import base64
import datetime
import io
import json
import logging
import time
from io import StringIO
from operator import index

import boto3
import streamlit as st
from botocore.exceptions import ClientError
from PIL import Image


# Configure logging
class ImageError(Exception):
    "Custom exception for errors returned by Amazon Titan Image Generator G1"


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

MODEL_ID = "amazon.titan-image-generator-v2:0"


def generate_image(body):
    """
    Generate an image using Amazon Titan Image Generator G1 model on demand.
    Args:
        body (str) : The request body to use.
    Returns:
        image_bytes (bytes): The image generated by the model.
    """

    logger.info(
        "Generating image with Amazon Titan Image Generator G1 model %s", MODEL_ID
    )

    bedrock_runtime = boto3.client(service_name="bedrock-runtime")

    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
    )
    response_body = json.loads(response.get("body").read())
    base64_image = response_body.get("images")[0]
    base64_bytes = base64_image.encode("ascii")
    image_bytes = base64.b64decode(base64_bytes)

    finish_reason = response_body.get("error")

    if finish_reason is not None:
        raise ImageError(f"Image generation error. Error is {finish_reason}")

    logger.info(
        "Successfully generated image with Amazon Titan Image Generator G1 v2 model %s",
        MODEL_ID,
    )

    return image_bytes


# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-image.html#model-parameters-titan-image-api
def prepare_outpainting_request_with_mask_prompt(
    source_image_path,
    mask_prompt,
    positive_prompt,
    negative_prompt,
    outpainting_mode,
    cfg_scale,
    seed,
    # image_width,
    # image_height
):
    """
    Prepare the request body for outpainting with mask prompt.
    Args:
        source_image_path (str): The path to the source image.
        mask_prompt (str): The mask prompt to use.
        positive_prompt (str): The positive prompt to use.
        negative_prompt (str): The negative prompt to use.
        outpainting_mode (str): The outpainting mode to use.
        cfg_scale (float): The CFG scale to use.
        seed (int): The seed to use.
        image_width (int): The width of the source image.
        image_height (int): The height of the source image.
    Returns:
        generated_image_path (str): The path to the generated image.
    """

    try:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        # Read image from file and encode as base64 strings.
        with open(source_image_path, "rb") as image_file:
            input_image = base64.b64encode(image_file.read()).decode("utf8")

        body = json.dumps(
            {
                "taskType": "OUTPAINTING",
                "outPaintingParams": {
                    "text": positive_prompt,
                    "negativeText": negative_prompt,
                    "image": input_image,
                    "maskPrompt": mask_prompt,
                    "outPaintingMode": outpainting_mode,
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    # "height": image_height,
                    # "width": image_height,
                    "cfgScale": cfg_scale,
                    "seed": seed,
                },
            }
        )

        image_bytes = generate_image(body=body)
        image = Image.open(io.BytesIO(image_bytes))
        epoch_time = int(time.time())
        generated_image_path = f"output/outpainting_{seed}_{epoch_time}.jpg"
        image.save(generated_image_path)
        logger.info(f"Generated image saved to {generated_image_path}")
        return generated_image_path
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
    except ImageError as err:
        logger.error("A image error occurred: " + format(err))


def display_response(source_image_path, generated_image_path, analysis_time):
    """Display the response from the model.
    Args:
        source_image_path (str): The path to the source image.
        generated_image_path (str): The path to the generated image.
        analysis_time (float): The time taken to analyze the image.
    Returns:
        None
    """
    st.image(source_image_path, caption="Source Image", use_column_width=True)
    st.image(generated_image_path, caption="Generated Image", use_column_width=True)

    generated_image = f"Generated image: {generated_image_path}"
    analysis_time_str = f"Response time: {analysis_time:.2f} seconds"
    st.text(f"{analysis_time_str}\n{generated_image}")


def main():
    image_width = 0
    image_height = 0

    st.set_page_config(page_title="Streamlit-Bedrock-Titan Application Example")

    hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>"""

    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    st.markdown("### Image Background Replacement on Amazon Bedrock")
    st.markdown(
        "Example of using outpainting to replace the background of an image using Amazon Titan Image Generator v2 on Amazon Bedrock. Uses promptable visual segmentation as opposed to a pre-existing image mask."
    )

    with st.form("my_form"):
        st.markdown("Inference Parameters")

        img = st.file_uploader("Upload Source Image", type=["jpg", "jpeg", "png"])

        if img is not None:
            image = Image.open(img)
            image_width = image.width
            image_height = image.height

            col1, col2 = st.columns(2)
            with col1:
                st.image(img, caption="Source Image", use_column_width=True)
            with col2:
                st.text(
                    f"Type: {img.type}\nSize (KB): {round(img.size/1024, 2)}\nMode: {image.mode}\nWidth: {image.width}\nHeight: {image.height}"
                )
            image_bytes = img.getvalue()
            source_image_path = f"./tmp/{img.name}"
            with open(source_image_path, "wb") as f:
                f.write(image_bytes)

        mask_prompt = st.text_input(
            label="Mask",
            value="Cheeseburger",
        )

        positive_prompt = st.text_area(
            height=150,
            label="Positive",
            value="A red checkered empty blanket spreads on the lush green grass of a park. A white round plate on the center of the blanket. In the background, a park's mature trees provide shade. Sun-dappled blue skies, a happy scene.",
        )

        negative_prompt = st.text_area(
            height=150,
            label="Negative",
            value="people, humans, animals, worst quality, low quality, low res, oversaturated, undersaturated, overexposed, underexposed, grayscale, b&w, bad photo, bad photography, bad art, watermark, signature, blur, blurry, grainy, ugly, asymmetrical, poorly lit, bad shadow, draft, cropped, out of frame, cut off, censored, jpeg artifacts, out of focus, glitch, duplicate, airbrushed, cartoon, anime, semi-realistic, cgi, render, blender, digital art, manga, amateur, 3D",
        )

        col1, col2 = st.columns(2)
        with col1:
            cfg_scale = st.slider(
                "CFG Scale", min_value=1.1, max_value=10.0, value=7.0, step=0.1
            )
        with col2:
            seed = st.slider(
                "Seed",
                min_value=0,
                max_value=2147483647,
                value=1761198479,
                step=1,
            )

        outpainting_mode = st.radio(
            label="Outpainting Mode",
            options=["DEFAULT", "PRECISE"],
            index=1,
            horizontal=True,
        )

        st.divider()

        submitted = st.form_submit_button("Submit")

        if (
            submitted
            and img is not None
            and image_height <= 1408
            and image_width <= 1408
        ):
            with st.spinner():
                start_time = datetime.datetime.now()
                generated_image_path = prepare_outpainting_request_with_mask_prompt(
                    source_image_path,
                    mask_prompt,
                    positive_prompt,
                    negative_prompt,
                    outpainting_mode,
                    cfg_scale,
                    seed,
                    # source_image_width,
                    # source_image_height
                )
                end_time = datetime.datetime.now()
                analysis_time = (end_time - start_time).total_seconds()
                if generated_image_path:
                    display_response(
                        source_image_path, generated_image_path, analysis_time
                    )
                else:
                    logger.error("Failed to get a valid response from the model.")
        if (
            submitted
            and img is not None
            and (image_height > 1408 or image_width > 1408)
        ):
            st.error(
                "Please upload an image with height and width less than or equal to 1408 pixels."
            )
        if submitted and img is None:
            st.error("Please upload an image file.")


if __name__ == "__main__":
    main()
